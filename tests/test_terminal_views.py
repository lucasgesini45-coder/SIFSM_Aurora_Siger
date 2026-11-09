"""Testes da visualização terminal: apresentação não altera dados nem métricas."""
import pandas as pd
import pytest

from src.simulation import gerar_simulacao
from src.regression import calcular_regressao
from src.terminal_views import menu_csv, mostrar_regressao, resumo_csv, resumo_por_dia, tabela_csv


def test_visualizacoes_csv_sem_modificar_dataframe(capsys):
    dados = gerar_simulacao()
    copia = dados.copy(deep=True)
    resumo_csv(dados)
    resumo_por_dia(dados)
    tabela_csv(dados, 0, 10)
    texto = capsys.readouterr().out
    assert "168" in texto
    assert "Geração" in texto
    assert "Balanço energético por dia" in texto.upper().title() or "BALANÇO ENERGÉTICO POR DIA" in texto
    assert "Registros do CSV".upper() in texto
    pd.testing.assert_frame_equal(dados, copia)


def test_menu_csv_paginacao_e_navegacao(monkeypatch, capsys):
    dados = gerar_simulacao()
    respostas = iter(["1", "2", "3", "4", "5", "6", "2", "0"])
    monkeypatch.setattr("builtins.input", lambda _="": next(respostas))
    menu_csv(dados)
    output = capsys.readouterr().out
    assert "REGISTROS DO CSV" in output
    assert "BALANÇO ENERGÉTICO" in output
    assert "INTERVALOS DO DIA 2" in output


def test_menu_csv_rejeita_colunas_incompletas():
    with pytest.raises(ValueError, match="colunas"):
        menu_csv(pd.DataFrame({"hora": [0]}))


def test_regressao_formatada_preserva_resultados(capsys):
    resultado = calcular_regressao(gerar_simulacao())
    copia = resultado.copy()
    mostrar_regressao(resultado)
    output = capsys.readouterr().out
    assert "MAE" in output and "RMSE" in output and "R²" in output
    assert "EQUAÇÃO" in output
    assert resultado == copia


def test_regressao_sem_r2_ajustavel(capsys):
    dados = pd.DataFrame({"hora": range(20), "consumo_kw": [5.0] * 20})
    resultado = calcular_regressao(dados)
    mostrar_regressao(resultado)
    assert "N/D" in capsys.readouterr().out
