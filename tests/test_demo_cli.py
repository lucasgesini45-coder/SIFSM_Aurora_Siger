"""Teste de demonstração automatizada dos menus exibidos no terminal do SIFSM.

Não usa credenciais, servidor Oracle, Arduino ou VS Code. Emula o teclado
para detectar erros na navegação real dos menus Python.
"""
from pathlib import Path

import pandas as pd

import codigo_fonte
from src import reports
from src.simulation import gerar_simulacao, exportar_csv


def _teclado(monkeypatch, comandos):
    respostas = iter(comandos)

    def digitar(prompt=""):
        try:
            return next(respostas)
        except StopIteration as exc:
            raise AssertionError(f"Menu pediu uma entrada inesperada: {prompt}") from exc

    monkeypatch.setattr("builtins.input", digitar)


def test_fluxo_completo_csv_regressao_terminal(monkeypatch, tmp_path, capsys):
    """Abre o menu real, gera CSV, consulta páginas e calcula a regressão."""
    destino = tmp_path / "dados_aurora_siger.csv"
    monkeypatch.setattr(codigo_fonte, "ARQUIVO_CSV", destino)
    _teclado(monkeypatch, [
        "2",        # menu principal: simulação
        "1", "",    # gerar 168 horas; pausa
        "2",        # consulta CSV
        "1",        # resumo
        "2",        # balanço por dia
        "3",        # primeira página
        "4",        # próxima página
        "6", "4",   # buscar dia 4
        "0", "",    # sai de consulta; pausa do submenu
        "3", "",    # regressão; pausa
        "0",        # volta do submenu
        "0",        # encerra
    ])
    codigo_fonte.main()

    saida = capsys.readouterr().out
    assert destino.exists(), "CSV não foi criado pela interface"
    dados = pd.read_csv(destino)
    assert len(dados) == 168
    assert dados["hora"].tolist() == list(range(168))
    assert "BALANÇO ENERGÉTICO" in saida
    assert "REGRESSÃO LINEAR" in saida
    assert "RMSE" in saida and "MAE" in saida
    assert "INTERVALOS DO DIA 4" in saida
    assert "Encerrando o SIFSM" in saida


def test_fluxo_circuito_logico_terminal(monkeypatch, capsys):
    """Confere tabela verdade, alerta ativo e texto de arquitetura."""
    _teclado(monkeypatch, [
        "6",  # menu circuitos
        "2", "",  # tabela verdade
        "1", "1", "1", "0", "",  # A=1 B=1 C=0 -> alerta
        "3", "",  # explicação arquitetura
        "0",  # volta
        "0",  # encerra
    ])
    codigo_fonte.main()
    saida = capsys.readouterr().out
    assert "TABELA VERDADE" in saida
    assert "ALERTA ATIVO" in saida
    assert "ARQUITETURA COMPUTACIONAL" in saida


def test_fluxo_relatorios_terminal(monkeypatch, tmp_path, capsys):
    """Os relatórios devem consultar um CSV válido sem Oracle."""
    destino = tmp_path / "dados_aurora_siger.csv"
    exportar_csv(gerar_simulacao(), destino)
    monkeypatch.setattr(reports, "CSV_SIMULACAO", destino)
    monkeypatch.setattr(reports, "PASTA_RELATORIOS", tmp_path / "relatorios")
    _teclado(monkeypatch, [
        "4",   # menu relatórios
        "1", "",  # resumo
        "4", "",  # alertas
        "3", "",  # exportação
        "0", "0",
    ])
    codigo_fonte.main()
    saida = capsys.readouterr().out
    assert "RESUMO ENERGÉTICO" in saida
    assert "ALERTAS DA SIMULAÇÃO" in saida
    assert (tmp_path / "relatorios" / "resumo_energetico_por_dia.csv").exists()


def test_fluxo_oracle_com_repositorio_simulado(monkeypatch, tmp_path, capsys):
    """Opção 2->4 recebe 168 registros e mostra resposta do pipeline.

    Este é apenas um teste da interface; a conexão real é verificada separadamente.
    """
    from src import persistence_pipeline

    destino = tmp_path / "dados_aurora_siger.csv"
    monkeypatch.setattr(codigo_fonte, "ARQUIVO_CSV", destino)
    chamadas = []

    def persistencia_falsa(dados, nome, data_inicio):
        chamadas.append((len(dados), nome, str(data_inicio)))
        return {
            "simulacao_id": 71,
            "regressao_id": 72,
            "intervalos": 168,
            "r2_treino_oracle": 0.15,
            "r2_teste_local": -0.01,
        }

    monkeypatch.setattr(persistence_pipeline, "persistir_simulacao", persistencia_falsa)
    _teclado(monkeypatch, [
        "2", "4", "Teste_Video_CLI", "2026-11-09", "", "0", "0",
    ])
    codigo_fonte.main()
    saida = capsys.readouterr().out
    assert chamadas == [(168, "Teste_Video_CLI", "2026-11-09")]
    assert destino.exists()
    assert "gravadas no Oracle" in saida
    assert "168" in saida
