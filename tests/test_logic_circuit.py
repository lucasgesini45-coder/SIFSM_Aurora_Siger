"""Validação exaustiva da regra booleana do alerta energético."""
from itertools import product

import pytest

from src.logic_circuit import avaliar_alerta, tabela_verdade, exibir_tabela, simular_entrada


@pytest.mark.parametrize("a,b,c", list(product((False, True), repeat=3)))
def test_todas_as_combinacoes(a, b, c):
    assert avaliar_alerta(a, b, c) is ((a and b) or c)


def test_tabela_verdade_oito_combinacoes():
    linhas = tabela_verdade()
    assert len(linhas) == 8
    assert len({(x["A"], x["B"], x["C"]) for x in linhas}) == 8
    assert sum(x["alerta"] for x in linhas) == 3


@pytest.mark.parametrize("entrada", [(0, False, False), ("1", False, False), (None, False, False)])
def test_rejeita_tipos_invalidos(entrada):
    with pytest.raises(ValueError, match="booleanas"):
        avaliar_alerta(*entrada)


def test_exibe_tabela(capsys):
    exibir_tabela()
    saida = capsys.readouterr().out
    assert "TABELA VERDADE" in saida
    assert "ALERTA = (A AND B) OR C" in saida


def test_simulacao_de_alerta(monkeypatch, capsys):
    respostas = iter(["1", "1", "0"])
    monkeypatch.setattr("builtins.input", lambda _="": next(respostas))
    assert simular_entrada() is True
    saida = capsys.readouterr().out
    assert "ALERTA ATIVO" in saida
    assert "nenhum dispositivo físico" in saida


def test_repergunta_entrada_invalida(monkeypatch, capsys):
    respostas = iter(["x", "0", "0", "0"])
    monkeypatch.setattr("builtins.input", lambda _="": next(respostas))
    assert simular_entrada() is False
    assert "Entrada inválida" in capsys.readouterr().out
