"""Exibição legível para o terminal: CSV, regressão e tabelas resumidas.

Somente apresentação: não altera os dados, os cálculos nem o banco Oracle.
"""
from math import isfinite

CAMPOS_CSV = (
    ("hora", "Hora", 5),
    ("dia", "Dia", 4),
    ("hora_dia", "H. dia", 6),
    ("geracao_kw", "Geração", 9),
    ("consumo_kw", "Consumo", 9),
    ("saldo_kwh", "Saldo", 9),
    ("soc_pct", "Bateria %", 10),
    ("deficit_kwh", "Déficit", 9),
    ("alerta", "Alerta", 7),
)


def titulo(texto):
    print("\n" + "=" * 78)
    print("  " + texto.upper())
    print("=" * 78)


def _numero(valor, casas=2):
    try:
        numero = float(valor)
        return f"{numero:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".") if isfinite(numero) else "N/D"
    except (TypeError, ValueError, OverflowError):
        return "N/D"


def _alerta(valor):
    if isinstance(valor, str):
        return "SIM" if valor.strip().lower() in {"true", "1", "sim"} else "NÃO"
    return "SIM" if bool(valor) else "NÃO"


def _linha_csv(registro):
    saida = []
    for chave, _, largura in CAMPOS_CSV:
        valor = registro[chave]
        if chave == "alerta":
            texto = _alerta(valor)
        elif chave in {"hora", "dia", "hora_dia"}:
            texto = str(int(valor))
        else:
            texto = _numero(valor)
        saida.append(f"{texto:>{largura}}")
    return " | ".join(saida)


def tabela_csv(dados, inicio=0, quantidade=10):
    """Mostra só 9 colunas essenciais para caber melhor no terminal."""
    titulo(f"Registros do CSV | {inicio + 1} a {min(inicio + quantidade, len(dados))} de {len(dados)}")
    cabecalho = " | ".join(f"{rotulo:>{largura}}" for _, rotulo, largura in CAMPOS_CSV)
    print(cabecalho)
    print("-" * len(cabecalho))
    for _, registro in dados.iloc[inicio:inicio + quantidade].iterrows():
        print(_linha_csv(registro))
    print("\nValores simulados. Energia em kWh para intervalos de 1 hora.")


def resumo_csv(dados):
    titulo("Resumo dos dados CSV")
    print(f"  Intervalos analisados : {len(dados)}")
    print(f"  Geração acumulada     : {_numero(dados['geracao_kw'].sum())} kWh")
    print(f"  Consumo acumulado     : {_numero(dados['consumo_kw'].sum())} kWh")
    print(f"  Saldo acumulado       : {_numero((dados['geracao_kw'] - dados['consumo_kw']).sum())} kWh")
    if "deficit_kwh" in dados:
        print(f"  Déficit não atendido  : {_numero(dados['deficit_kwh'].sum())} kWh")
    if "soc_pct" in dados and len(dados):
        print(f"  Bateria ao final      : {_numero(dados['soc_pct'].iloc[-1], 1)}%")
    if "alerta" in dados:
        print(f"  Intervalos em alerta  : {sum(_alerta(v) == 'SIM' for v in dados['alerta'])}")
    print("\n  Fonte: CSV local; dados sintéticos, não são medições reais.")


def resumo_por_dia(dados):
    if "dia" not in dados or dados.empty:
        print("Não há informação de dias disponível.")
        return
    titulo("Balanço energético por dia")
    print(" Dia | Horas | Geração kWh | Consumo kWh | Saldo kWh | Alertas")
    print("-" * 68)
    for dia, grupo in dados.groupby("dia", sort=True):
        geracao = float(grupo["geracao_kw"].sum())
        consumo = float(grupo["consumo_kw"].sum())
        alertas = sum(_alerta(v) == "SIM" for v in grupo["alerta"]) if "alerta" in grupo else 0
        print(f"{int(dia):>4} | {len(grupo):>5} | {_numero(geracao):>11} | "
              f"{_numero(consumo):>11} | {_numero(geracao - consumo):>9} | {alertas:>7}")


def menu_csv(dados):
    """Navegação em páginas sem despejar as 168 linhas de uma vez."""
    obrigatorios = {chave for chave, _, _ in CAMPOS_CSV}
    if dados.empty or not obrigatorios.issubset(dados.columns):
        raise ValueError("CSV vazio ou com colunas obrigatórias ausentes.")
    posicao = 0
    tamanho = 10
    while True:
        print("\n--- CONSULTA DO CSV LOCAL ---")
        print("1. Visão geral")
        print("2. Resumo por dia")
        print("3. Ver registros (10 por página)")
        print("4. Próxima página")
        print("5. Página anterior")
        print("6. Buscar dia (1-7)")
        print("0. Voltar")
        escolha = input("Escolha uma opção: ").strip()
        if escolha == "0":
            return
        if escolha == "1":
            resumo_csv(dados)
        elif escolha == "2":
            resumo_por_dia(dados)
        elif escolha in {"3", "4", "5"}:
            if escolha == "4":
                posicao = min(posicao + tamanho, (len(dados) - 1) // tamanho * tamanho)
            elif escolha == "5":
                posicao = max(0, posicao - tamanho)
            tabela_csv(dados, posicao, tamanho)
        elif escolha == "6":
            texto = input("Número do dia: ").strip()
            if not texto.isdigit():
                print("Informe um dia numérico válido.")
                continue
            dia = int(texto)
            filtro = dados.loc[dados["dia"] == dia]
            if filtro.empty:
                print(f"Nenhum intervalo encontrado para o dia {dia}.")
                continue
            titulo(f"Intervalos do dia {dia}")
            cabecalho = " | ".join(f"{rotulo:>{largura}}" for _, rotulo, largura in CAMPOS_CSV)
            print(cabecalho)
            print("-" * len(cabecalho))
            for _, registro in filtro.iterrows():
                print(_linha_csv(registro))
        else:
            print("Opção inválida.")


def mostrar_regressao(resultado):
    """Apresenta exatamente os indicadores do cálculo, sem recomputar métricas."""
    titulo("Análise de regressão linear")
    x = resultado["variavel_x"]
    y = resultado["variavel_y"]
    print("  MODELO E DADOS")
    print(f"  Variável explicativa : {x} (hora)")
    print(f"  Variável prevista    : {y} (kW)")
    print(f"  Amostras de treino   : {resultado['n_treino']}")
    print(f"  Amostras de teste    : {resultado['n_teste']}")
    print("\n  EQUAÇÃO AJUSTADA (somente dados de treino)")
    print(f"  {y} = ({resultado['coeficiente_angular']:+.6f} × {x}) "
          f"{resultado['intercepto']:+.6f}")
    print("\n  QUALIDADE NO CONJUNTO DE TESTE")
    print(f"  MAE   (erro absoluto médio) : {_numero(resultado['mae_kw'], 4)} kW")
    print(f"  RMSE  (erro quadrático)     : {_numero(resultado['rmse_kw'], 4)} kW")
    r2 = resultado.get("r2_teste")
    print(f"  R²    (teste temporal)      : {_numero(r2, 4) if r2 is not None else 'N/D (consumo de teste constante)'}")
    print(f"  MAE da referência (média)   : {_numero(resultado['mae_baseline_kw'], 4)} kW")
    if r2 is not None and r2 < 0:
        print("  Atenção: R² negativo significa desempenho inferior à referência de média no teste.")
    if resultado["mae_kw"] > resultado["mae_baseline_kw"]:
        print("  Atenção: neste teste, a referência pela média teve MAE menor.")
    print("\n  PREVISÃO DIDÁTICA")
    print(f"  Hora projetada          : {_numero(resultado['hora_prevista'], 0)}")
    print(f"  Consumo estimado        : {_numero(resultado['consumo_previsto_kw'], 3)} kW")
    print("\n  INTERPRETAÇÃO")
    print("  MAE/RMSE menores indicam menor erro. R² de teste pode ser negativo.")
    print("  A regressão usa consumo x hora e não representa o ciclo diário completo.")
    print(f"  {resultado['observacao']}")
    print("  Este relatório local não grava a regressão automaticamente no Oracle.")
