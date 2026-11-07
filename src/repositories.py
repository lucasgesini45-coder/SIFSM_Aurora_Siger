"""CRUD das tabelas do banco_aurora_siger.sql (SIMULACAO, INTERVALO_HORARIO,
REGRESSAO_RESULTADO e RECOMENDACAO_IA).

Convenções:
- inserir_*   devolve o id gerado (inserir_intervalos_lote devolve a quantidade).
- buscar_*    devolve um dicionário, ou None se não existir.
- listar_*    devolve lista de dicionários (chaves em minúsculas).
- atualizar_* e excluir_* levantam RegistroNaoEncontrado se o id não existir.
- Entrada inválida levanta ValueError ANTES de acessar o banco.
- Falhas do banco levantam ErroBanco (ou subclasses; veja src/database.py).
- Todas aceitam `conexao=` opcional: se informada, a função NÃO faz commit
  (a transação é de quem abriu a conexão, via database.transacao()).
"""
import math
from datetime import date, datetime, timedelta

from src.database import (
    RegistroNaoEncontrado,
    consultar,
    executar,
    executar_lote,
    inserir_retornando_id,
    transacao,
)

STATUS_SIMULACAO = ("CRIADA", "EXECUTADA", "ANALISADA")
TIPOS_RECOMENDACAO = ("EXPLICACAO", "RECOMENDACAO", "ALERTA")
INTERVALOS_POR_DIA = 24

COLUNAS_SIMULACAO = "id, nome, data_inicio, dias, total_intervalos, semente, status, criado_em"
COLUNAS_INTERVALO = (
    "id, simulacao_id, numero_intervalo, dia, hora, data_hora, "
    "temperatura_c, irradiancia_wm2, geracao_kwh, consumo_kwh, saldo_kwh"
)
COLUNAS_REGRESSAO = (
    "id, simulacao_id, variavel_x, variavel_y, coef_angular, intercepto, "
    "r_quadrado, n_observacoes, criado_em"
)
COLUNAS_RECOMENDACAO = "id, simulacao_id, modelo, tipo, texto, criado_em"


# ---------------------------------------------------------------------------
# Validação de entradas (espelha os CHECK/NOT NULL do script SQL)
# ---------------------------------------------------------------------------
def _texto(valor, campo, maximo=None):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{campo}: informe um texto não vazio.")
    valor = valor.strip()
    if maximo is not None and len(valor) > maximo:
        raise ValueError(f"{campo}: no máximo {maximo} caracteres.")
    return valor


def _inteiro(valor, campo, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ValueError(f"{campo}: informe um número inteiro.")
    try:
        if isinstance(valor, float) and not valor.is_integer():
            raise ValueError
        numero = int(valor)  # aceita int, str numérica e tipos do numpy
    except (TypeError, ValueError):
        raise ValueError(f"{campo}: informe um número inteiro.") from None
    if (minimo is not None and numero < minimo) or (maximo is not None and numero > maximo):
        raise ValueError(f"{campo}: deve estar entre {minimo} e {maximo}.")
    return numero


def _decimal(valor, campo, minimo=None, maximo=None):
    if isinstance(valor, bool):
        raise ValueError(f"{campo}: informe um número.")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{campo}: informe um número.") from None
    if not math.isfinite(numero):
        raise ValueError(f"{campo}: valores ausentes (NaN) ou infinitos não são aceitos.")
    if (minimo is not None and numero < minimo) or (maximo is not None and numero > maximo):
        limites = f"entre {minimo} e {maximo}" if maximo is not None else f"maior ou igual a {minimo}"
        raise ValueError(f"{campo}: deve ser {limites}.")
    return numero


def _data(valor, campo):
    """Aceita datetime/date ou texto AAAA-MM-DD / DD/MM/AAAA."""
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time())
    if isinstance(valor, str):
        for formato in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(valor.strip(), formato)
            except ValueError:
                continue
    raise ValueError(f"{campo}: informe uma data válida (AAAA-MM-DD ou DD/MM/AAAA).")


def _opcao(valor, campo, permitidos):
    texto = _texto(valor, campo).upper()
    if texto not in permitidos:
        raise ValueError(f"{campo}: use um destes valores: {', '.join(permitidos)}.")
    return texto


def _id(valor, campo="id"):
    return _inteiro(valor, campo, minimo=1, maximo=10**18)


def _validar_campos(campos, regras, obrigatorio=False):
    """Valida um dict de campos contra {nome: função_validadora}."""
    desconhecidos = sorted(set(campos) - set(regras))
    if desconhecidos:
        raise ValueError(
            f"Campo(s) não permitido(s): {', '.join(desconhecidos)}. "
            f"Permitidos: {', '.join(regras)}."
        )
    if obrigatorio:
        faltando = [c for c in regras if c not in campos]
        if faltando:
            raise ValueError(f"Campo(s) obrigatório(s) ausente(s): {', '.join(faltando)}.")
    return {nome: regras[nome](valor) for nome, valor in campos.items()}


# ---------------------------------------------------------------------------
# Rotinas genéricas (nomes de tabela/coluna vêm só das constantes deste arquivo)
# ---------------------------------------------------------------------------
def _buscar(tabela, colunas, id_registro, conexao):
    linhas = consultar(
        f"SELECT {colunas} FROM {tabela} WHERE id = :id_registro",
        {"id_registro": _id(id_registro)},
        conexao,
    )
    return linhas[0] if linhas else None


def _atualizar(tabela, rotulo, id_registro, campos, regras, conexao):
    if not campos:
        raise ValueError("Informe ao menos um campo para atualizar.")
    validados = _validar_campos(campos, regras)
    id_registro = _id(id_registro)
    atribuicoes = ", ".join(f"{coluna} = :{coluna}" for coluna in validados)
    afetadas = executar(
        f"UPDATE {tabela} SET {atribuicoes} WHERE id = :id_registro",
        {**validados, "id_registro": id_registro},
        conexao,
    )
    if afetadas == 0:
        raise RegistroNaoEncontrado(f"{rotulo} {id_registro} não encontrada.")


def _excluir(tabela, rotulo, id_registro, conexao):
    id_registro = _id(id_registro)
    afetadas = executar(
        f"DELETE FROM {tabela} WHERE id = :id_registro", {"id_registro": id_registro}, conexao
    )
    if afetadas == 0:
        raise RegistroNaoEncontrado(f"{rotulo} {id_registro} não encontrada.")


# ===========================================================================
# SIMULACAO
# ===========================================================================
_REGRAS_SIMULACAO = {
    "nome": lambda v: _texto(v, "nome", 100),
    "data_inicio": lambda v: _data(v, "data_inicio"),
    "semente": lambda v: _inteiro(v, "semente", 0, 9_999_999_999),
    "status": lambda v: _opcao(v, "status", STATUS_SIMULACAO),
}


def inserir_simulacao(nome, data_inicio, semente=42, status="CRIADA", conexao=None):
    """Cadastra uma simulação (7 dias / 168 intervalos, fixos pelo esquema). Devolve o id."""
    dados = _validar_campos(
        {"nome": nome, "data_inicio": data_inicio, "semente": semente, "status": status},
        _REGRAS_SIMULACAO,
        obrigatorio=True,
    )
    return inserir_retornando_id(
        "INSERT INTO simulacao (nome, data_inicio, semente, status) "
        "VALUES (:nome, :data_inicio, :semente, :status)",
        dados,
        conexao,
    )


def buscar_simulacao(simulacao_id, conexao=None):
    return _buscar("simulacao", COLUNAS_SIMULACAO, simulacao_id, conexao)


def buscar_simulacao_por_nome(nome, conexao=None):
    linhas = consultar(
        f"SELECT {COLUNAS_SIMULACAO} FROM simulacao WHERE nome = :nome",
        {"nome": _texto(nome, "nome", 100)},
        conexao,
    )
    return linhas[0] if linhas else None


def listar_simulacoes(status=None, limite=100, conexao=None):
    """Lista simulações, da mais recente para a mais antiga."""
    parametros = {"limite": _inteiro(limite, "limite", 1, 1000)}
    filtro = ""
    if status is not None:
        parametros["status"] = _opcao(status, "status", STATUS_SIMULACAO)
        filtro = "WHERE status = :status "
    return consultar(
        f"SELECT {COLUNAS_SIMULACAO} FROM simulacao {filtro}"
        "ORDER BY id DESC FETCH FIRST :limite ROWS ONLY",
        parametros,
        conexao,
    )


def atualizar_simulacao(simulacao_id, conexao=None, **campos):
    """Altera nome, data_inicio, semente e/ou status. Ex.: atualizar_simulacao(1, status="EXECUTADA")."""
    _atualizar("simulacao", "Simulação", simulacao_id, campos, _REGRAS_SIMULACAO, conexao)


def excluir_simulacao(simulacao_id, conexao=None):
    """Exclui a simulação e, em cascata, seus intervalos, regressões e recomendações."""
    _excluir("simulacao", "Simulação", simulacao_id, conexao)


# ===========================================================================
# INTERVALO_HORARIO
# ===========================================================================
_REGRAS_INTERVALO_EDITAVEL = {
    "temperatura_c": lambda v: _decimal(v, "temperatura_c", -999.99, 999.99),
    "irradiancia_wm2": lambda v: _decimal(v, "irradiancia_wm2", 0, 99999.99),
    "geracao_kwh": lambda v: _decimal(v, "geracao_kwh", 0),
    "consumo_kwh": lambda v: _decimal(v, "consumo_kwh", 0),
}


def _montar_intervalo(simulacao_id, dados, inicio, posicao=None):
    """Valida um intervalo e deriva dia, hora e data_hora a partir do número (1..168)."""
    rotulo = f"Intervalo #{posicao}: " if posicao is not None else ""
    if not isinstance(dados, dict):
        raise ValueError(f"{rotulo}esperado um dicionário com os campos do intervalo.")
    permitidos = {"numero_intervalo", "data_hora", *_REGRAS_INTERVALO_EDITAVEL}
    faltando = [c for c in ("numero_intervalo", *_REGRAS_INTERVALO_EDITAVEL) if c not in dados]
    extras = sorted(set(dados) - permitidos)
    if faltando or extras:
        raise ValueError(
            f"{rotulo}campos ausentes: {faltando or 'nenhum'}; campos desconhecidos: {extras or 'nenhum'}."
        )
    try:
        numero = _inteiro(dados["numero_intervalo"], "numero_intervalo", 1, 168)
        validados = _validar_campos(
            {c: dados[c] for c in _REGRAS_INTERVALO_EDITAVEL}, _REGRAS_INTERVALO_EDITAVEL
        )
        data_hora = (
            _data(dados["data_hora"], "data_hora")
            if dados.get("data_hora") is not None
            else inicio + timedelta(hours=numero - 1)
        )
    except ValueError as exc:
        raise ValueError(f"{rotulo}{exc}") from None
    return {
        "simulacao_id": simulacao_id,
        "numero_intervalo": numero,
        "dia": (numero - 1) // INTERVALOS_POR_DIA + 1,
        "hora": (numero - 1) % INTERVALOS_POR_DIA,
        "data_hora": data_hora,
        **validados,
    }


_SQL_INSERIR_INTERVALO = (
    "INSERT INTO intervalo_horario (simulacao_id, numero_intervalo, dia, hora, data_hora, "
    "temperatura_c, irradiancia_wm2, geracao_kwh, consumo_kwh) VALUES "
    "(:simulacao_id, :numero_intervalo, :dia, :hora, :data_hora, "
    ":temperatura_c, :irradiancia_wm2, :geracao_kwh, :consumo_kwh)"
)


def _data_inicio_da_simulacao(simulacao_id, conexao):
    simulacao = buscar_simulacao(simulacao_id, conexao)
    if simulacao is None:
        raise RegistroNaoEncontrado(f"Simulação {simulacao_id} não encontrada.")
    return simulacao["data_inicio"]


def inserir_intervalo(simulacao_id, numero_intervalo, temperatura_c, irradiancia_wm2,
                      geracao_kwh, consumo_kwh, data_hora=None, conexao=None):
    """Cadastra um intervalo horário. dia/hora/data_hora são calculados se omitidos. Devolve o id."""
    simulacao_id = _id(simulacao_id, "simulacao_id")
    dados = {
        "numero_intervalo": numero_intervalo, "temperatura_c": temperatura_c,
        "irradiancia_wm2": irradiancia_wm2, "geracao_kwh": geracao_kwh,
        "consumo_kwh": consumo_kwh, "data_hora": data_hora,
    }
    # Valida tudo antes de consultar o banco (data_inicio só é necessária se data_hora faltar).
    _montar_intervalo(simulacao_id, dados, datetime.min)
    with transacao(conexao) as con:  # leitura da simulação + INSERT na mesma transação
        inicio = _data_inicio_da_simulacao(simulacao_id, con)
        return inserir_retornando_id(
            _SQL_INSERIR_INTERVALO, _montar_intervalo(simulacao_id, dados, inicio), con
        )


def inserir_intervalos_lote(simulacao_id, intervalos, conexao=None):
    """Cadastra vários intervalos de uma vez (tudo ou nada). Devolve a quantidade inserida.

    `intervalos`: lista de dicts com numero_intervalo, temperatura_c, irradiancia_wm2,
    geracao_kwh, consumo_kwh e, opcionalmente, data_hora.
    """
    simulacao_id = _id(simulacao_id, "simulacao_id")
    if not isinstance(intervalos, (list, tuple)) or not intervalos:
        raise ValueError("intervalos: informe uma lista não vazia.")
    # Validação completa antes de gravar qualquer linha.
    for posicao, dados in enumerate(intervalos, start=1):
        _montar_intervalo(simulacao_id, dados, datetime.min, posicao)
    numeros = [int(d["numero_intervalo"]) for d in intervalos]
    if len(set(numeros)) != len(numeros):
        raise ValueError("intervalos: há números de intervalo repetidos.")
    with transacao(conexao) as con:  # leitura da simulação + INSERTs na mesma transação
        inicio = _data_inicio_da_simulacao(simulacao_id, con)
        linhas = [_montar_intervalo(simulacao_id, d, inicio, p) for p, d in enumerate(intervalos, 1)]
        executar_lote(_SQL_INSERIR_INTERVALO, linhas, con)
    return len(linhas)


def buscar_intervalo(intervalo_id, conexao=None):
    return _buscar("intervalo_horario", COLUNAS_INTERVALO, intervalo_id, conexao)


def listar_intervalos(simulacao_id, dia=None, conexao=None):
    """Lista os intervalos de uma simulação (opcionalmente de um dia, 1 a 7), em ordem."""
    parametros = {"simulacao_id": _id(simulacao_id, "simulacao_id")}
    filtro = ""
    if dia is not None:
        parametros["dia"] = _inteiro(dia, "dia", 1, 7)
        filtro = " AND dia = :dia"
    return consultar(
        f"SELECT {COLUNAS_INTERVALO} FROM intervalo_horario "
        f"WHERE simulacao_id = :simulacao_id{filtro} ORDER BY numero_intervalo",
        parametros,
        conexao,
    )


def resumir_por_dia(simulacao_id, conexao=None):
    """Totais por dia (geração, consumo e saldo em kWh) de uma simulação."""
    return consultar(
        "SELECT dia, COUNT(*) AS intervalos, ROUND(SUM(geracao_kwh), 2) AS geracao_kwh, "
        "ROUND(SUM(consumo_kwh), 2) AS consumo_kwh, ROUND(SUM(saldo_kwh), 2) AS saldo_kwh "
        "FROM intervalo_horario WHERE simulacao_id = :simulacao_id GROUP BY dia ORDER BY dia",
        {"simulacao_id": _id(simulacao_id, "simulacao_id")},
        conexao,
    )


def atualizar_intervalo(intervalo_id, conexao=None, **campos):
    """Altera temperatura_c, irradiancia_wm2, geracao_kwh e/ou consumo_kwh (saldo é recalculado pelo banco)."""
    _atualizar("intervalo_horario", "Intervalo", intervalo_id, campos,
               _REGRAS_INTERVALO_EDITAVEL, conexao)


def excluir_intervalo(intervalo_id, conexao=None):
    _excluir("intervalo_horario", "Intervalo", intervalo_id, conexao)


# ===========================================================================
# REGRESSAO_RESULTADO
# ===========================================================================
_REGRAS_REGRESSAO = {
    "variavel_x": lambda v: _texto(v, "variavel_x", 50),
    "variavel_y": lambda v: _texto(v, "variavel_y", 50),
    "coef_angular": lambda v: _decimal(v, "coef_angular"),
    "intercepto": lambda v: _decimal(v, "intercepto"),
    "r_quadrado": lambda v: _decimal(v, "r_quadrado", 0, 1),  # CHECK ck_reg_r2
    "n_observacoes": lambda v: _inteiro(v, "n_observacoes", 2, 9999),  # CHECK ck_reg_n
}


def inserir_regressao(simulacao_id, variavel_x, variavel_y, coef_angular,
                      intercepto, r_quadrado, n_observacoes, conexao=None):
    """Grava o resultado de uma regressão vinculada a uma simulação. Devolve o id."""
    dados = _validar_campos(
        {"variavel_x": variavel_x, "variavel_y": variavel_y, "coef_angular": coef_angular,
         "intercepto": intercepto, "r_quadrado": r_quadrado, "n_observacoes": n_observacoes},
        _REGRAS_REGRESSAO,
        obrigatorio=True,
    )
    dados["simulacao_id"] = _id(simulacao_id, "simulacao_id")
    return inserir_retornando_id(
        "INSERT INTO regressao_resultado (simulacao_id, variavel_x, variavel_y, coef_angular, "
        "intercepto, r_quadrado, n_observacoes) VALUES (:simulacao_id, :variavel_x, :variavel_y, "
        ":coef_angular, :intercepto, :r_quadrado, :n_observacoes)",
        dados,
        conexao,
    )


def buscar_regressao(regressao_id, conexao=None):
    return _buscar("regressao_resultado", COLUNAS_REGRESSAO, regressao_id, conexao)


def listar_regressoes(simulacao_id, conexao=None):
    return consultar(
        f"SELECT {COLUNAS_REGRESSAO} FROM regressao_resultado "
        "WHERE simulacao_id = :simulacao_id ORDER BY id DESC",
        {"simulacao_id": _id(simulacao_id, "simulacao_id")},
        conexao,
    )


def atualizar_regressao(regressao_id, conexao=None, **campos):
    _atualizar("regressao_resultado", "Regressão", regressao_id, campos, _REGRAS_REGRESSAO, conexao)


def excluir_regressao(regressao_id, conexao=None):
    _excluir("regressao_resultado", "Regressão", regressao_id, conexao)


# ===========================================================================
# RECOMENDACAO_IA
# ===========================================================================
_REGRAS_RECOMENDACAO = {
    "modelo": lambda v: _texto(v, "modelo", 80),
    "tipo": lambda v: _opcao(v, "tipo", TIPOS_RECOMENDACAO),
    "texto": lambda v: _texto(v, "texto"),
}


def inserir_recomendacao(simulacao_id, modelo, tipo, texto, conexao=None):
    """Grava uma resposta/recomendação da IA para auditoria. Devolve o id."""
    dados = _validar_campos(
        {"modelo": modelo, "tipo": tipo, "texto": texto}, _REGRAS_RECOMENDACAO, obrigatorio=True
    )
    dados["simulacao_id"] = _id(simulacao_id, "simulacao_id")
    return inserir_retornando_id(
        "INSERT INTO recomendacao_ia (simulacao_id, modelo, tipo, texto) "
        "VALUES (:simulacao_id, :modelo, :tipo, :texto)",
        dados,
        conexao,
    )


def buscar_recomendacao(recomendacao_id, conexao=None):
    return _buscar("recomendacao_ia", COLUNAS_RECOMENDACAO, recomendacao_id, conexao)


def listar_recomendacoes(simulacao_id, tipo=None, conexao=None):
    parametros = {"simulacao_id": _id(simulacao_id, "simulacao_id")}
    filtro = ""
    if tipo is not None:
        parametros["tipo"] = _opcao(tipo, "tipo", TIPOS_RECOMENDACAO)
        filtro = " AND tipo = :tipo"
    return consultar(
        f"SELECT {COLUNAS_RECOMENDACAO} FROM recomendacao_ia "
        f"WHERE simulacao_id = :simulacao_id{filtro} ORDER BY id DESC",
        parametros,
        conexao,
    )


def atualizar_recomendacao(recomendacao_id, conexao=None, **campos):
    _atualizar("recomendacao_ia", "Recomendação", recomendacao_id, campos,
               _REGRAS_RECOMENDACAO, conexao)


def excluir_recomendacao(recomendacao_id, conexao=None):
    _excluir("recomendacao_ia", "Recomendação", recomendacao_id, conexao)


# ===========================================================================
# Demonstração do CRUD: python -m src.repositories
# Cria uma simulação temporária, percorre cadastrar/listar/alterar/excluir,
# mostra o tratamento de erros e remove tudo no final.
# ===========================================================================
def _demonstracao():
    from src.database import ErroBanco, ErroIntegridade

    nome = f"DEMO_CRUD_{datetime.now():%Y%m%d_%H%M%S}"
    sim_id = None
    try:
        print("1) CADASTRAR")
        sim_id = inserir_simulacao(nome, date.today())
        inserir_intervalo(sim_id, 1, 22.5, 0, 0, 2.1)
        inserir_intervalo(sim_id, 2, 23.0, 150, 1.2, 2.0)
        print(f"   simulação {sim_id} criada com 2 intervalos")

        print("2) LISTAR")
        for i in listar_intervalos(sim_id):
            print(f"   intervalo {i['numero_intervalo']}: ger={i['geracao_kwh']} "
                  f"con={i['consumo_kwh']} saldo={i['saldo_kwh']}")

        print("3) ALTERAR")
        atualizar_simulacao(sim_id, status="EXECUTADA")
        atualizar_intervalo(listar_intervalos(sim_id)[0]["id"], consumo_kwh=2.5)
        print("   status =", buscar_simulacao(sim_id)["status"])

        print("4) TRATAMENTO DE ERROS")
        for descricao, acao in (
            ("nome duplicado", lambda: inserir_simulacao(nome, date.today())),
            ("dia inválido (dia 9)", lambda: listar_intervalos(sim_id, dia=9)),
            ("id inexistente", lambda: atualizar_simulacao(999999999, status="ANALISADA")),
            ("r² fora de 0..1", lambda: inserir_regressao(sim_id, "x", "y", 1, 0, 1.5, 10)),
        ):
            try:
                acao()
            except (ValueError, ErroIntegridade, ErroBanco) as erro:
                print(f"   {descricao}: {type(erro).__name__} -> {erro}")
    except ErroBanco as erro:
        print(f"Falha de banco: {erro}")
    finally:
        if sim_id is not None:
            print("5) EXCLUIR")
            excluir_simulacao(sim_id)  # cascata remove os intervalos
            print("   simulação de demonstração removida")


if __name__ == "__main__":
    _demonstracao()
