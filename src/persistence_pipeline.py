"""Persistência transacional da simulação de 168 horas e regressão no Oracle.

O CSV local e o esquema Oracle representam fontes distintas até esta gravação.
A regressão de teste pode ter R² negativo; o campo Oracle guarda o R² do
ajuste no conjunto de treinamento, explicitamente identificado no retorno.
"""
from datetime import date
import numpy as np
import pandas as pd

from src import repositories as repo
from src.database import transacao
from src.regression import calcular_regressao

COLUNAS = (
    "hora", "temperatura_c", "irradiancia_wm2", "geracao_kw", "consumo_kw"
)


def preparar_intervalos(dados):
    """Valida todos os intervalos ANTES da primeira operação SQL."""
    if not isinstance(dados, pd.DataFrame) or len(dados) != 168:
        raise ValueError("Persistência Oracle requer uma simulação de exatamente 168 horas.")
    if not set(COLUNAS).issubset(dados.columns):
        raise ValueError("A simulação deve conter hora, temperatura, irradiância, geração e consumo.")
    horas = dados["hora"].tolist()
    if horas != list(range(168)):
        raise ValueError("Horas da simulação devem estar ordenadas de 0 a 167.")
    try:
        valores = dados[list(COLUNAS)].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Os campos numéricos da simulação devem conter números.") from exc
    if not np.isfinite(valores).all():
        raise ValueError("Dados da simulação contêm valores inválidos.")
    # Limites físicos e precisão das colunas NUMBER no esquema Oracle.
    if (dados[["irradiancia_wm2", "geracao_kw", "consumo_kw"]].to_numpy(dtype=float) < 0).any():
        raise ValueError("Irradiância, geração e consumo não podem ser negativos.")
    if (valores[:, 1] < -999.99).any() or (valores[:, 1] > 999.99).any():
        raise ValueError("Temperatura fora do intervalo suportado pelo Oracle.")
    if (valores[:, 2] > 99999.99).any():
        raise ValueError("Irradiância excede a precisão da coluna Oracle.")
    if (valores[:, 3:5] > 9999999.999).any():
        raise ValueError("Geração ou consumo excedem a precisão da coluna Oracle.")
    intervalos = []
    for _, item in dados.iterrows():
        intervalos.append({
            "numero_intervalo": int(item["hora"]) + 1,
            "temperatura_c": float(item["temperatura_c"]),
            "irradiancia_wm2": float(item["irradiancia_wm2"]),
            "geracao_kwh": float(item["geracao_kw"]),
            "consumo_kwh": float(item["consumo_kw"]),
        })
    return intervalos


def calcular_r2_treino(dados, resultado):
    """R² do ajuste no TREINO, não a métrica temporal r2_teste."""
    treino = int(resultado["n_treino"])
    tabela = dados[["hora", "consumo_kw"]].sort_values("hora").iloc[:treino]
    x = tabela["hora"].to_numpy(dtype=float)
    y = tabela["consumo_kw"].to_numpy(dtype=float)
    previsto = resultado["coeficiente_angular"] * x + resultado["intercepto"]
    sst = float(np.sum((y - y.mean()) ** 2))
    if sst <= 0:
        return 1.0 if np.allclose(y, previsto) else 0.0
    # Diferenças de arredondamento de ponto flutuante.
    return min(1.0, max(0.0, float(1.0 - np.sum((y - previsto) ** 2) / sst)))


def persistir_simulacao(dados, nome, data_inicio=None):
    """Grava 168 intervalos + regressão na mesma transação.

    Não recria tabelas, não altera uma simulação anterior e não muda o
    funcionamento da IA. Em qualquer erro, o Oracle desfaz a transação.
    """
    intervalos = preparar_intervalos(dados)
    resultado = calcular_regressao(dados)
    r2_treino = calcular_r2_treino(dados, resultado)
    if not isinstance(nome, str) or not nome.strip():
        raise ValueError("Informe um nome para a simulação.")
    inicio = date.today() if data_inicio is None else data_inicio
    with transacao() as conexao:
        simulacao_id = repo.inserir_simulacao(
            nome.strip(), inicio, semente=42, status="CRIADA", conexao=conexao
        )
        quantidade = repo.inserir_intervalos_lote(
            simulacao_id, intervalos, conexao=conexao
        )
        regressao_id = repo.inserir_regressao(
            simulacao_id,
            resultado["variavel_x"],
            resultado["variavel_y"],
            resultado["coeficiente_angular"],
            resultado["intercepto"],
            r2_treino,
            len(dados),
            conexao=conexao,
        )
        repo.atualizar_simulacao(simulacao_id, status="ANALISADA", conexao=conexao)
    return {
        "simulacao_id": simulacao_id,
        "regressao_id": regressao_id,
        "intervalos": quantidade,
        "r2_treino_oracle": r2_treino,
        "r2_teste_local": resultado["r2_teste"],
    }
