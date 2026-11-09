"""Testes da camada de persistência (config, database, repositories).

Não precisam de Oracle: a conexão é substituída por um objeto falso que
registra os comandos SQL e os parâmetros enviados. A validação contra o
Oracle real é feita com `python -m src.database` e `python -m src.repositories`.
"""
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import oracledb
import pytest

from src import config, database, repositories as repo
from src.database import (
    ErroBanco, ErroConexao, ErroIntegridade, ErroTransacao, RegistroNaoEncontrado,
)


# ---------------------------------------------------------------- doubles
class CursorFalso:
    def __init__(self, con):
        self.con = con
        self.arraysize = 100
        self.rowcount = con.rowcount
        self.description = None
        self._linhas = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def var(self, tipo, **kwargs):
        return SimpleNamespace(getvalue=lambda: [self.con.novo_id])

    def execute(self, sql, params=None):
        self.con.comandos.append((sql, params))
        if self.con.erro_execute:
            raise self.con.erro_execute
        if self.con.respostas:
            colunas, linhas = self.con.respostas.pop(0)
            self.description = [(c,) for c in colunas]
            self._linhas = linhas

    def executemany(self, sql, lista):
        self.con.comandos.append((sql, lista))

    def fetchall(self):
        return self._linhas

    def fetchone(self):
        return self._linhas[0] if self._linhas else None


class ConexaoFalsa:
    version = "23.0"
    username = "APP"

    def __init__(self, rowcount=1, novo_id=7, respostas=None, erro_execute=None):
        self.rowcount, self.novo_id = rowcount, novo_id
        self.respostas, self.erro_execute = list(respostas or []), erro_execute
        self.comandos, self.commits, self.rollbacks, self.fechada = [], 0, 0, False

    def cursor(self):
        return CursorFalso(self)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.fechada = True


def erro_oracle(codigo, mensagem, classe=oracledb.DatabaseError):
    info = SimpleNamespace(code=codigo, full_code=f"ORA-{codigo:05d}", message=mensagem)
    return classe(info)


@pytest.fixture
def con(monkeypatch):
    falsa = ConexaoFalsa()
    monkeypatch.setattr(database, "conectar", lambda: falsa)
    return falsa


# ---------------------------------------------------------------- config
def test_config_sem_variaveis_levanta_erro(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ARQUIVO_ENV", tmp_path / "inexistente.env")
    for v in config.VARIAVEIS_OBRIGATORIAS:
        monkeypatch.delenv(v, raising=False)
    with pytest.raises(config.ErroConfiguracao, match="ORACLE_USER"):
        config.obter_config()


def test_config_le_env_sem_sobrescrever_terminal(monkeypatch, tmp_path):
    arquivo = tmp_path / ".env"
    arquivo.write_text(
        "# comentário\nORACLE_USER=app\nexport ORACLE_PASSWORD='s#nha 1'\nORACLE_DSN=h:1521/s\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "ARQUIVO_ENV", arquivo)
    monkeypatch.delenv("ORACLE_PASSWORD", raising=False)
    monkeypatch.delenv("ORACLE_DSN", raising=False)
    monkeypatch.setenv("ORACLE_USER", "do_terminal")
    monkeypatch.delenv("ORACLE_TIMEOUT", raising=False)
    cfg = config.obter_config()
    assert cfg.usuario == "do_terminal"  # terminal vence o .env
    assert cfg.senha == "s#nha 1"
    assert cfg.timeout_s == config.TIMEOUT_PADRAO_S
    assert "s#nha" not in repr(cfg)  # senha não vaza em repr


def test_config_timeout_invalido(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ARQUIVO_ENV", tmp_path / "x.env")
    monkeypatch.setenv("ORACLE_USER", "u")
    monkeypatch.setenv("ORACLE_PASSWORD", "p")
    monkeypatch.setenv("ORACLE_DSN", "d")
    monkeypatch.setenv("ORACLE_TIMEOUT", "abc")
    with pytest.raises(config.ErroConfiguracao):
        config.obter_config()


# ---------------------------------------------------------------- transação
def test_transacao_commit_e_fecha(con):
    with database.transacao() as c:
        assert c is con
    assert (con.commits, con.rollbacks, con.fechada) == (1, 0, True)


def test_transacao_rollback_em_erro_e_fecha(con):
    with pytest.raises(RuntimeError):
        with database.transacao():
            raise RuntimeError("falha")
    assert (con.commits, con.rollbacks, con.fechada) == (0, 1, True)


def test_transacao_com_conexao_recebida_nao_commita_nem_fecha():
    externa = ConexaoFalsa()
    with database.transacao(externa):
        pass
    assert (externa.commits, externa.rollbacks, externa.fechada) == (0, 0, False)


def test_erro_do_driver_vira_erro_do_projeto(con):
    with pytest.raises(ErroBanco):
        with database.transacao():
            raise erro_oracle(942, "ORA-00942: table or view does not exist")
    assert con.rollbacks == 1


@pytest.mark.parametrize("codigo,mensagem,classe", [
    (1, "ORA-00001: unique constraint (APP.UQ_SIMULACAO_NOME) violated", ErroIntegridade),
    (2291, "ORA-02291: integrity constraint (APP.FK_X) violated - parent key not found", ErroIntegridade),
    (2290, "ORA-02290: check constraint (APP.CK_REG_R2) violated", ErroIntegridade),
    (60, "ORA-00060: deadlock detected", ErroTransacao),
    (1017, "ORA-01017: invalid credential", ErroConexao),
    (12541, "ORA-12541: no listener", ErroConexao),
])
def test_traducao_de_codigos_ora(codigo, mensagem, classe):
    erro = database.traduzir_erro(erro_oracle(codigo, mensagem))
    assert type(erro) is classe


def test_traducao_cita_restricao_sem_expor_schema():
    erro = database.traduzir_erro(
        erro_oracle(1, "ORA-00001: unique constraint (APP.UQ_SIMULACAO_NOME) violated")
    )
    assert "UQ_SIMULACAO_NOME" in str(erro) and "APP." not in str(erro)


def test_verificar_conexao_ok(con):
    estado = database.verificar_conexao()
    assert estado["conectado"] and estado["versao"] == "23.0" and estado["erro"] is None


def test_verificar_conexao_sem_config_nao_levanta(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ARQUIVO_ENV", tmp_path / "x.env")
    for v in config.VARIAVEIS_OBRIGATORIAS:
        monkeypatch.delenv(v, raising=False)
    estado = database.verificar_conexao()
    assert not estado["conectado"] and "ORACLE_USER" in estado["erro"]


# ---------------------------------------------------------------- repositories: validação
@pytest.mark.parametrize("chamada", [
    lambda: repo.inserir_simulacao("", "2025-01-06"),
    lambda: repo.inserir_simulacao("x" * 101, "2025-01-06"),
    lambda: repo.inserir_simulacao("ok", "06-99-2025"),
    lambda: repo.inserir_simulacao("ok", "2025-01-06", status="INVALIDO"),
    lambda: repo.inserir_simulacao("ok", "2025-01-06", semente=True),
    lambda: repo.buscar_simulacao(0),
    lambda: repo.buscar_simulacao("abc"),
    lambda: repo.listar_simulacoes(limite=0),
    lambda: repo.listar_intervalos(1, dia=8),
    lambda: repo.atualizar_simulacao(1),                     # sem campos
    lambda: repo.atualizar_simulacao(1, id=5),               # campo não permitido
    lambda: repo.atualizar_intervalo(1, geracao_kwh=-1),
    lambda: repo.atualizar_intervalo(1, consumo_kwh=float("nan")),
    lambda: repo.inserir_regressao(1, "x", "y", 1, 0, 1.5, 10),   # r² > 1 (CHECK)
    lambda: repo.inserir_regressao(1, "x", "y", 1, 0, 0.5, 1),    # n < 2 (CHECK)
    lambda: repo.inserir_recomendacao(1, "m", "OUTRO", "t"),
    lambda: repo.inserir_intervalos_lote(1, []),
])
def test_entrada_invalida_levanta_valueerror_sem_tocar_no_banco(chamada, monkeypatch):
    def proibido():
        raise AssertionError("não deveria conectar")
    monkeypatch.setattr(database, "conectar", proibido)
    with pytest.raises(ValueError):
        chamada()


# ---------------------------------------------------------------- repositories: SQL e parâmetros
def test_inserir_simulacao_usa_binds_e_devolve_id(con):
    novo = repo.inserir_simulacao("  Teste  ", "2025-01-06", semente=np.int64(42))
    sql, params = con.comandos[0]
    assert novo == 7 and con.commits == 1
    assert "RETURNING id INTO :novo_id" in sql and "Teste" not in sql  # valor não vai no SQL
    assert params["nome"] == "Teste" and params["data_inicio"] == datetime(2025, 1, 6)
    assert type(params["semente"]) is int  # numpy -> int nativo


def test_injecao_de_sql_fica_como_texto_no_parametro(con):
    repo.inserir_simulacao("x'; DROP TABLE simulacao; --", "2025-01-06")
    sql, params = con.comandos[0]
    assert "DROP" not in sql and "DROP" in params["nome"]


def test_atualizar_monta_set_dinamico_so_com_campos_permitidos(con):
    repo.atualizar_simulacao(3, status="executada", nome="Novo")
    sql, params = con.comandos[0]
    assert sql == "UPDATE simulacao SET status = :status, nome = :nome WHERE id = :id_registro"
    assert params == {"status": "EXECUTADA", "nome": "Novo", "id_registro": 3}


def test_atualizar_e_excluir_inexistente_levantam_nao_encontrado(monkeypatch):
    monkeypatch.setattr(database, "conectar", lambda: ConexaoFalsa(rowcount=0))
    with pytest.raises(RegistroNaoEncontrado):
        repo.atualizar_simulacao(99, status="CRIADA")
    with pytest.raises(RegistroNaoEncontrado):
        repo.excluir_simulacao(99)


def test_buscar_inexistente_devolve_none(monkeypatch):
    falsa = ConexaoFalsa(respostas=[(["ID"], [])])
    monkeypatch.setattr(database, "conectar", lambda: falsa)
    assert repo.buscar_simulacao(99) is None


def test_consulta_devolve_dicionarios_com_chaves_minusculas(monkeypatch):
    falsa = ConexaoFalsa(respostas=[(["ID", "NOME"], [(1, "A"), (2, "B")])])
    monkeypatch.setattr(database, "conectar", lambda: falsa)
    assert repo.listar_simulacoes() == [{"id": 1, "nome": "A"}, {"id": 2, "nome": "B"}]


def test_lote_deriva_dia_hora_data_e_converte_tipos(monkeypatch):
    inicio = datetime(2025, 1, 6)
    falsa = ConexaoFalsa(respostas=[(["ID", "DATA_INICIO"], [(1, inicio)])])
    monkeypatch.setattr(database, "conectar", lambda: falsa)
    itens = [
        {"numero_intervalo": np.int64(n), "temperatura_c": np.float64(20.5),
         "irradiancia_wm2": 0, "geracao_kwh": 0.0, "consumo_kwh": 2}
        for n in (1, 25, 168)
    ]
    assert repo.inserir_intervalos_lote(1, itens) == 3
    linhas = falsa.comandos[-1][1]
    assert [(l["dia"], l["hora"]) for l in linhas] == [(1, 0), (2, 0), (7, 23)]
    assert linhas[1]["data_hora"] == datetime(2025, 1, 7)
    assert type(linhas[0]["numero_intervalo"]) is int
    assert falsa.commits == 1


def test_lote_invalido_nao_grava_nada(monkeypatch):
    falsa = ConexaoFalsa()
    monkeypatch.setattr(database, "conectar", lambda: falsa)
    bom = {"numero_intervalo": 1, "temperatura_c": 20, "irradiancia_wm2": 0,
           "geracao_kwh": 0, "consumo_kwh": 2}
    ruim = {**bom, "numero_intervalo": 169}
    with pytest.raises(ValueError, match="#2"):
        repo.inserir_intervalos_lote(1, [bom, ruim])
    with pytest.raises(ValueError, match="repetidos"):
        repo.inserir_intervalos_lote(1, [bom, dict(bom)])
    assert falsa.comandos == []


def test_lote_simulacao_inexistente(monkeypatch):
    monkeypatch.setattr(database, "conectar", lambda: ConexaoFalsa(respostas=[(["ID"], [])]))
    item = {"numero_intervalo": 1, "temperatura_c": 20, "irradiancia_wm2": 0,
            "geracao_kwh": 0, "consumo_kwh": 2}
    with pytest.raises(RegistroNaoEncontrado):
        repo.inserir_intervalos_lote(1, [item])


def test_operacoes_na_mesma_transacao_nao_commitam_sozinhas(con):
    with database.transacao(con) as externa:
        repo.inserir_simulacao("A", "2025-01-06", conexao=externa)
        repo.excluir_simulacao(7, conexao=externa)
        assert externa.commits == 0
    assert con.commits == 0  # dono é quem abriu (aqui, o teste)


def test_violacao_de_unicidade_vira_erro_de_integridade(monkeypatch):
    falsa = ConexaoFalsa(erro_execute=erro_oracle(
        1, "ORA-00001: unique constraint (APP.UQ_SIMULACAO_NOME) violated"))
    monkeypatch.setattr(database, "conectar", lambda: falsa)
    with pytest.raises(ErroIntegridade):
        repo.inserir_simulacao("Repetida", "2025-01-06")
    assert falsa.rollbacks == 1 and falsa.fechada
