"""Conexão Python com o Oracle, transações e tradução de erros.

Uso típico (uma operação = uma transação, com commit/rollback automáticos):

    from src.database import consultar
    linhas = consultar("SELECT id, nome FROM simulacao")

Várias operações na MESMA transação (tudo ou nada):

    from src.database import transacao
    from src import repositories as repo

    with transacao() as con:
        sim_id = repo.inserir_simulacao("Teste", "2025-01-06", conexao=con)
        repo.inserir_intervalos_lote(sim_id, intervalos, conexao=con)
    # commit aqui; se algo falhar dentro do with, rollback de tudo.

Todos os erros do driver são convertidos em subclasses de ErroBanco, com
mensagens em português e sem expor senha.
"""
import re
from contextlib import contextmanager

import oracledb

from src.config import ErroConfiguracao, obter_config


# ---------------------------------------------------------------------------
# Exceções do projeto
# ---------------------------------------------------------------------------
class ErroBanco(Exception):
    """Base de todos os erros de banco de dados do SIFSM."""


class ErroConexao(ErroBanco):
    """Banco inacessível, credenciais inválidas ou configuração ausente."""


class ErroTransacao(ErroBanco):
    """Falha ao confirmar/desfazer uma transação (deadlock, recurso ocupado...)."""


class ErroIntegridade(ErroBanco):
    """Violação de restrição: duplicidade, chave estrangeira, CHECK, NOT NULL."""


class RegistroNaoEncontrado(ErroBanco):
    """UPDATE/DELETE que não encontrou o registro informado."""


# ---------------------------------------------------------------------------
# Tradução de erros do Oracle
# ---------------------------------------------------------------------------
# Códigos ORA- que indicam problema de conexão/sessão.
_ORA_CONEXAO = {
    1017: "usuário ou senha inválidos",
    28000: "conta bloqueada",
    28001: "senha expirada",
    1033: "Oracle em inicialização ou desligamento",
    1034: "Oracle indisponível",
    3113: "conexão encerrada pelo servidor",
    3114: "sem conexão com o Oracle",
    12154: "DSN não pôde ser resolvido",
    12170: "tempo de conexão esgotado",
    12514: "serviço não conhecido pelo listener",
    12541: "listener não encontrado (host/porta incorretos)",
    12543: "host inacessível",
    12545: "host ou serviço inexistente",
    12537: "conexão encerrada pelo listener",
}
# Códigos ORA- de transação.
_ORA_TRANSACAO = {
    60: "deadlock detectado; tente novamente",
    54: "registro em uso por outra sessão; tente novamente",
    30006: "recurso ocupado; tente novamente",
}
# Códigos ORA- de integridade (mensagem amigável).
_ORA_INTEGRIDADE = {
    1: "já existe um registro com esse valor único",
    1400: "campo obrigatório não informado",
    1407: "campo obrigatório não pode ficar vazio",
    1438: "valor numérico excede a precisão da coluna",
    1722: "valor numérico inválido",
    2290: "valor viola uma regra de validação (CHECK)",
    2291: "registro pai inexistente (ex.: simulação não encontrada)",
    2292: "existem registros filhos vinculados",
    12899: "texto maior que o tamanho da coluna",
}


def _detalhes(exc):
    """Extrai (código numérico, código completo, mensagem curta) do erro do driver."""
    info = exc.args[0] if exc.args else None
    codigo = getattr(info, "code", None)
    completo = getattr(info, "full_code", "") or ""
    mensagem = getattr(info, "message", None) or str(exc)
    primeira_linha = str(mensagem).strip().splitlines()[0] if str(mensagem).strip() else ""
    return codigo, completo, primeira_linha


def traduzir_erro(exc):
    """Converte uma exceção do oracledb em ErroBanco (ou subclasse)."""
    codigo, completo, mensagem = _detalhes(exc)
    eh_ora = completo.startswith("ORA-") or (not completo and codigo is not None)
    tecnico = f" [{completo or codigo}]" if (completo or codigo) else ""

    if isinstance(exc, (oracledb.InterfaceError, oracledb.OperationalError)) or (
        eh_ora and codigo in _ORA_CONEXAO
    ):
        motivo = _ORA_CONEXAO.get(codigo, "falha de comunicação com o Oracle")
        return ErroConexao(f"Falha de conexão com o Oracle: {motivo}.{tecnico}")
    if eh_ora and codigo in _ORA_TRANSACAO:
        return ErroTransacao(f"Falha na transação: {_ORA_TRANSACAO[codigo]}.{tecnico}")
    if eh_ora and codigo in _ORA_INTEGRIDADE:
        restricao = re.search(r"\(([^)]+)\)", mensagem)
        extra = f" (restrição {restricao.group(1).split('.')[-1]})" if restricao else ""
        return ErroIntegridade(f"Integridade dos dados: {_ORA_INTEGRIDADE[codigo]}{extra}.")
    return ErroBanco(f"Erro no banco Oracle:{tecnico} {mensagem}".strip())


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------
def _ler_clob_como_texto(cursor, metadata):
    """Faz colunas CLOB (recomendacao_ia.texto) virem como str, não como objeto LOB."""
    if metadata.type_code is oracledb.DB_TYPE_CLOB:
        return cursor.var(oracledb.DB_TYPE_LONG, arraysize=cursor.arraysize)
    return None


def conectar():
    """Abre uma conexão nova (sem autocommit). Quem chama deve fechá-la.

    Prefira transacao(), que cuida de commit, rollback e fechamento.
    """
    try:
        config = obter_config()
    except ErroConfiguracao as exc:
        raise ErroConexao(str(exc)) from exc
    try:
        conexao = oracledb.connect(**config.parametros())
    except oracledb.Error as exc:
        # Toda falha ao conectar é tratada como ErroConexao.
        erro = traduzir_erro(exc)
        if isinstance(erro, ErroConexao):
            raise erro from exc
        raise ErroConexao(str(erro)) from exc
    conexao.outputtypehandler = _ler_clob_como_texto
    return conexao


def _desfazer(conexao):
    """Rollback que nunca levanta exceção (a conexão pode já estar perdida)."""
    try:
        conexao.rollback()
    except Exception:
        pass


@contextmanager
def transacao(conexao=None):
    """Contexto transacional.

    - Sem argumento: abre conexão, faz COMMIT se o bloco terminar bem,
      ROLLBACK se der erro, e sempre fecha a conexão.
    - Com `conexao`: apenas reutiliza a conexão recebida; o commit/rollback
      e o fechamento ficam com quem a abriu (permite juntar várias operações
      em uma única transação).
    """
    dono = conexao is None
    con = conectar() if dono else conexao
    try:
        yield con
        if dono:
            con.commit()
    except ErroBanco:
        if dono:
            _desfazer(con)
        raise
    except oracledb.Error as exc:
        if dono:
            _desfazer(con)
        raise traduzir_erro(exc) from exc
    except Exception:
        if dono:
            _desfazer(con)
        raise
    finally:
        if dono:
            try:
                con.close()
            except Exception:
                pass  # já fechada ou perdida; nada a fazer


# ---------------------------------------------------------------------------
# Operações básicas (usadas por repositories.py)
# Os valores SEMPRE vão em parâmetros (:nome); nunca concatenados no SQL.
# ---------------------------------------------------------------------------
def consultar(sql, parametros=None, conexao=None):
    """Executa um SELECT e devolve lista de dicionários (chaves em minúsculas)."""
    with transacao(conexao) as con:
        with con.cursor() as cursor:
            cursor.execute(sql, parametros or {})
            colunas = [coluna[0].lower() for coluna in cursor.description]
            return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]


def executar(sql, parametros=None, conexao=None):
    """Executa INSERT/UPDATE/DELETE e devolve o nº de linhas afetadas."""
    with transacao(conexao) as con:
        with con.cursor() as cursor:
            cursor.execute(sql, parametros or {})
            return cursor.rowcount


def executar_lote(sql, lista_parametros, conexao=None):
    """Executa o mesmo comando para várias linhas (executemany), em uma transação."""
    if not lista_parametros:
        return 0
    with transacao(conexao) as con:
        with con.cursor() as cursor:
            cursor.executemany(sql, lista_parametros)
            return cursor.rowcount


def inserir_retornando_id(sql_insert, parametros, conexao=None):
    """INSERT em tabela com ID automático (IDENTITY); devolve o id gerado."""
    with transacao(conexao) as con:
        with con.cursor() as cursor:
            novo_id = cursor.var(oracledb.NUMBER)
            cursor.execute(
                sql_insert + " RETURNING id INTO :novo_id",
                {**parametros, "novo_id": novo_id},
            )
            valor = novo_id.getvalue()
            if isinstance(valor, list):  # DML RETURNING devolve lista
                valor = valor[0]
            return int(valor)


def verificar_conexao():
    """Testa a conexão com um SELECT 1. Nunca levanta exceção.

    Retorna: {"conectado": bool, "versao": str|None, "usuario": str|None, "erro": str|None}
    """
    resultado = {"conectado": False, "versao": None, "usuario": None, "erro": None}
    try:
        with transacao() as con:
            with con.cursor() as cursor:
                cursor.execute("SELECT 1 FROM dual")
                cursor.fetchone()
            resultado.update(conectado=True, versao=con.version, usuario=con.username)
    except ErroBanco as exc:
        resultado["erro"] = str(exc)
    return resultado


if __name__ == "__main__":  # python -m src.database
    estado = verificar_conexao()
    if estado["conectado"]:
        print(f"CONECTADO | Oracle {estado['versao']} | usuário {estado['usuario']}")
    else:
        print(f"FALHA: {estado['erro']}")
