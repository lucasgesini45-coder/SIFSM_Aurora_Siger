
def verificar_conexao_oracle():
    """Verifica a conexão com o banco Oracle."""
    from src.database import verificar_conexao

    return verificar_conexao()


def executar_simulacao(horas=168):
    """Executa a simulação pelo módulo responsável."""
    if not isinstance(horas, int) or isinstance(horas, bool) or horas <= 0:
        raise ValueError("A duração deve ser um número inteiro positivo.")

    from src.simulation import gerar_simulacao

    return gerar_simulacao(horas=horas)


def executar_regressao(dados):
    """Executa a análise de regressão."""
    from src.regression import calcular_regressao

    return calcular_regressao(dados)


def consultar_assistente(pergunta):
    """Envia uma pergunta para o assistente de IA."""
    if not isinstance(pergunta, str) or not pergunta.strip():
        raise ValueError("A pergunta não pode estar vazia.")

    from src.ai_assistant import responder_pergunta

    return responder_pergunta(pergunta.strip())
