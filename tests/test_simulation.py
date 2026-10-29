
import pytest

from src.services import executar_simulacao, consultar_assistente


def test_simulacao_rejeita_zero_horas():
    with pytest.raises(ValueError):
        executar_simulacao(0)


def test_simulacao_rejeita_horas_negativas():
    with pytest.raises(ValueError):
        executar_simulacao(-1)


def test_simulacao_rejeita_valor_decimal():
    with pytest.raises(ValueError):
        executar_simulacao(1.5)


def test_simulacao_rejeita_booleano():
    with pytest.raises(ValueError):
        executar_simulacao(True)


def test_assistente_rejeita_pergunta_vazia():
    with pytest.raises(ValueError):
        consultar_assistente("")


def test_assistente_rejeita_pergunta_com_espacos():
    with pytest.raises(ValueError):
        consultar_assistente("   ")
