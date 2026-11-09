"""Testes de integração da camada de persistência sem acesso ao Oracle real."""
from contextlib import contextmanager
from datetime import date
import pandas as pd
import pytest

from src.simulation import gerar_simulacao
from src.persistence_pipeline import preparar_intervalos, persistir_simulacao


def test_simulacao_contem_colunas_para_oracle():
    dados = gerar_simulacao()
    intervalos = preparar_intervalos(dados)
    assert len(intervalos) == 168
    assert intervalos[0]["numero_intervalo"] == 1
    assert intervalos[-1]["numero_intervalo"] == 168
    assert all(0 <= i["irradiancia_wm2"] for i in intervalos)
    assert all(i["geracao_kwh"] >= 0 and i["consumo_kwh"] >= 0 for i in intervalos)


def test_rejeita_dados_invalidos():
    with pytest.raises(ValueError, match="168"):
        preparar_intervalos(gerar_simulacao(24))
    dados = gerar_simulacao()
    dados.loc[0, "temperatura_c"] = float("nan")
    with pytest.raises(ValueError, match="inválidos"):
        preparar_intervalos(dados)


def test_persistencia_na_mesma_transacao(monkeypatch):
    from src import persistence_pipeline as pipeline
    chamadas = []
    conexao = object()

    @contextmanager
    def transacao_falsa():
        chamadas.append("iniciar")
        yield conexao
        chamadas.append("commit")

    def inserir_simulacao(*args, **kwargs):
        assert kwargs["conexao"] is conexao
        chamadas.append("simulacao")
        return 91

    def inserir_intervalos(simulacao_id, intervalos, conexao):
        assert simulacao_id == 91 and len(intervalos) == 168 and conexao is conexao_falsa
        chamadas.append("intervalos")
        return len(intervalos)

    conexao_falsa = conexao

    def inserir_regressao(*args, **kwargs):
        assert args[0] == 91 and kwargs["conexao"] is conexao
        assert 0 <= args[5] <= 1
        chamadas.append("regressao")
        return 42

    def atualizar(*args, **kwargs):
        assert kwargs["status"] == "ANALISADA"
        chamadas.append("status")

    monkeypatch.setattr(pipeline, "transacao", transacao_falsa)
    monkeypatch.setattr(pipeline.repo, "inserir_simulacao", inserir_simulacao)
    monkeypatch.setattr(pipeline.repo, "inserir_intervalos_lote", inserir_intervalos)
    monkeypatch.setattr(pipeline.repo, "inserir_regressao", inserir_regressao)
    monkeypatch.setattr(pipeline.repo, "atualizar_simulacao", atualizar)

    resultado = persistir_simulacao(gerar_simulacao(), "Teste novo", date(2026, 11, 9))
    assert resultado["simulacao_id"] == 91
    assert resultado["regressao_id"] == 42
    assert chamadas == ["iniciar", "simulacao", "intervalos", "regressao", "status", "commit"]


def test_falha_aborta_transacao(monkeypatch):
    from src import persistence_pipeline as pipeline
    eventos = []

    @contextmanager
    def transacao_falsa():
        eventos.append("iniciar")
        try:
            yield object()
        except RuntimeError:
            eventos.append("rollback")
            raise
        else:
            eventos.append("commit")

    monkeypatch.setattr(pipeline, "transacao", transacao_falsa)
    monkeypatch.setattr(pipeline.repo, "inserir_simulacao", lambda *a, **kw: 1)

    def falhar(*args, **kwargs):
        raise RuntimeError("falha controlada")

    monkeypatch.setattr(pipeline.repo, "inserir_intervalos_lote", falhar)
    with pytest.raises(RuntimeError, match="falha controlada"):
        persistir_simulacao(gerar_simulacao(), "Simulação teste")
    assert eventos == ["iniciar", "rollback"]
