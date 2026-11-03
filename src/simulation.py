"""Simulação didática de energia; hipóteses descritas no README."""
from pathlib import Path
import numpy as np
import pandas as pd

SEMENTE = 42
CAPACIDADE_KWH = 300.0
ENERGIA_INICIAL_KWH = 240.0
EFICIENCIA = 0.95


def gerar_simulacao(horas=168):
    """Retorna DataFrame; não grava nem altera o banco de dados.

    Cada linha representa [hora, hora+1), com energia ao final do intervalo.
    Reinicia o gerador local para garantir reprodutibilidade.
    """
    if isinstance(horas, bool) or not isinstance(horas, int) or horas < 1:
        raise ValueError('horas deve ser um inteiro positivo.')
    rng = np.random.default_rng(SEMENTE)
    energia = ENERGIA_INICIAL_KWH
    registros = []
    for hora in range(horas):
        dia, h = hora // 24 + 1, hora % 24
        tempestade = dia in (4, 5)
        # Consumo base 12 kW, ocupação diurna +4 kW e ruído limitado.
        consumo = 12.0 + (4.0 if 8 <= h < 20 else 0.0) + rng.uniform(-1, 1)
        solar = max(0.0, np.sin(np.pi * (h + 0.5 - 6) / 12)) if 6 <= h < 18 else 0.0
        geracao = 65.0 * solar * rng.uniform(0.9, 1.0) * (0.3 if tempestade else 1.0)
        # Intervalo de uma hora: energia (kWh) = potência média (kW) * 1 h.
        saldo = geracao - consumo
        inicio = energia
        if saldo >= 0:
            carga = min(saldo, (CAPACIDADE_KWH - energia) / EFICIENCIA)
            descarga = 0.0
            perda = carga * (1 - EFICIENCIA)
            excedente = saldo - carga
            deficit = 0.0
            energia += carga * EFICIENCIA
        else:
            carga = excedente = 0.0
            descarga = min(-saldo, energia * EFICIENCIA)
            perda = descarga * (1 / EFICIENCIA - 1)
            deficit = -saldo - descarga
            energia -= descarga / EFICIENCIA
        energia = float(np.clip(energia, 0, CAPACIDADE_KWH))
        registros.append(dict(hora=hora, dia=dia, hora_dia=h,
            tempestade=tempestade, geracao_kw=geracao, consumo_kw=consumo,
            saldo_kwh=saldo, bateria_inicio_kwh=inicio, bateria_fim_kwh=energia,
            soc_pct=100 * energia / CAPACIDADE_KWH, carga_kwh=carga,
            descarga_kwh=descarga, perdas_kwh=perda, excedente_kwh=excedente,
            deficit_kwh=deficit, alerta=(energia < 0.2 * CAPACIDADE_KWH or deficit > 1e-9)))
    return pd.DataFrame(registros)


def exportar_csv(dados, caminho='dados_aurora_siger.csv'):
    """CSV UTF-8, vírgula como separador e ponto decimal; retorna Path."""
    destino = Path(caminho)
    try:
        dados.to_csv(destino, index=False, encoding='utf-8', float_format='%.10f')
    except OSError as exc:
        raise OSError(f'Não foi possível gravar o CSV em {destino}.') from exc
    return destino


if __name__ == '__main__':
    dados = gerar_simulacao()
    destino = Path(__file__).resolve().parents[1] / 'dados_aurora_siger.csv'
    print(f'{len(dados)} registros exportados: {exportar_csv(dados, destino)}')
