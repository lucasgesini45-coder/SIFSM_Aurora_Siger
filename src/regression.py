"""Regressão linear simples por mínimos quadrados, usando NumPy."""
import numpy as np
import pandas as pd


def calcular_regressao(dados):
    """Estima consumo_kw em função de hora; devolve dicionário serializável.

    Reserva os últimos 20% para teste temporal. O modelo retornado é ajustado
    apenas no treino; comparação com média do treino expõe sua limitação.
    """
    if not isinstance(dados, pd.DataFrame):
        raise ValueError('dados deve ser um DataFrame.')
    if not {'hora', 'consumo_kw'}.issubset(dados.columns) or len(dados) < 10:
        raise ValueError('São necessárias hora, consumo_kw e pelo menos 10 linhas.')
    try:
        tabela = dados[['hora', 'consumo_kw']].astype(float).sort_values('hora')
    except (ValueError, TypeError) as exc:
        raise ValueError('Hora e consumo devem ser numéricos.') from exc
    if not np.isfinite(tabela.to_numpy()).all():
        raise ValueError('Não são aceitos valores ausentes ou infinitos.')
    x, y = tabela.to_numpy().T
    if (np.diff(x) <= 0).any() or (y < 0).any() or (x < 0).any():
        raise ValueError('Horas devem ser únicas e não negativas; consumo não negativo.')
    corte = int(len(x) * 0.8)
    xt, yt = x[:corte], y[:corte]
    a = float(np.sum((xt-xt.mean())*(yt-yt.mean())) / np.sum((xt-xt.mean())**2))
    b = float(yt.mean() - a * xt.mean())
    previsto = a * x[corte:] + b
    erro = y[corte:] - previsto
    sst = float(np.sum((y[corte:] - y[corte:].mean())**2))
    proxima = float(x[-1] + 1)
    return dict(variavel_x='hora', variavel_y='consumo_kw',
        coeficiente_angular=a, intercepto=b, n_treino=corte, n_teste=len(x)-corte,
        mae_kw=float(np.mean(abs(erro))), rmse_kw=float(np.sqrt(np.mean(erro**2))),
        r2_teste=float(1 - np.sum(erro**2)/sst) if sst > 0 else None,
        mae_baseline_kw=float(np.mean(abs(y[corte:] - yt.mean()))),
        hora_prevista=proxima, consumo_previsto_kw=float(a*proxima+b),
        observacao='Tendência linear didática: não representa o ciclo diário nem garante previsões operacionais.')


if __name__ == '__main__':
    import json
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    try:
        resultado = calcular_regressao(pd.read_csv(raiz / 'dados_aurora_siger.csv'))
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        raise SystemExit(f'Falha na análise: {exc}')
