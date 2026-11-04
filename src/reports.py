"""Relatórios de leitura do SIFSM, sem alterar dados Oracle."""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CSV_SIMULACAO = RAIZ / "dados_aurora_siger.csv"
PASTA_RELATORIOS = RAIZ / "relatorios"


def ler_dados():
    """Lê o CSV local e verifica campos mínimos."""
    if not CSV_SIMULACAO.exists() or CSV_SIMULACAO.stat().st_size == 0:
        raise ValueError("Não há CSV disponível. Execute a simulação em 2 -> 1.")
    try:
        dados = pd.read_csv(CSV_SIMULACAO)
    except (OSError, pd.errors.ParserError) as exc:
        raise ValueError(f"Falha ao ler o CSV: {exc}") from exc
    exigidas = {"hora", "dia", "geracao_kw", "consumo_kw", "deficit_kwh", "alerta", "soc_pct"}
    if not exigidas.issubset(dados.columns) or dados.empty:
        raise ValueError("CSV sem dados válidos ou com colunas ausentes.")
    return dados


def resumo_energetico():
    dados = ler_dados()
    geracao = float(dados["geracao_kw"].sum())
    consumo = float(dados["consumo_kw"].sum())
    print("\n" + "=" * 65)
    print("  RESUMO ENERGÉTICO — SIMULAÇÃO LOCAL")
    print("=" * 65)
    print(f"  Intervalos simulados : {len(dados)}")
    print(f"  Geração solar        : {geracao:.2f} kWh")
    print(f"  Consumo total        : {consumo:.2f} kWh")
    print(f"  Saldo geração-consumo: {geracao - consumo:+.2f} kWh")
    print(f"  Déficit não atendido : {dados['deficit_kwh'].sum():.2f} kWh")
    print(f"  Alertas registrados  : {int(dados['alerta'].sum())}")
    print(f"  Carga final bateria  : {float(dados['soc_pct'].iloc[-1]):.1f}%")
    print("-" * 65)
    print("  Valores sintéticos. Não representam medições reais.")


def historico_oracle():
    """Consulta apenas metadados das últimas simulações do schema Oracle."""
    import os
    import oracledb

    campos = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
    if any(not os.environ.get(c) for c in campos):
        raise ValueError("Oracle não configurado neste terminal. Defina ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN.")
    try:
        with oracledb.connect(
            user=os.environ["ORACLE_USER"],
            password=os.environ["ORACLE_PASSWORD"],
            dsn=os.environ["ORACLE_DSN"],
        ) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "SELECT id, nome, status, data_inicio FROM simulacao ORDER BY id DESC FETCH FIRST 10 ROWS ONLY"
                )
                linhas = cursor.fetchall()
    except oracledb.Error as exc:
        raise ValueError(f"Falha ao consultar o histórico Oracle: {exc}") from exc
    print("\n" + "=" * 65)
    print("  HISTÓRICO NO ORACLE (ÚLTIMAS 10 SIMULAÇÕES)")
    print("=" * 65)
    if not linhas:
        print("  Nenhuma simulação encontrada.")
    for identificador, nome, status, data in linhas:
        print(f"  #{identificador} | {nome} | {status} | {data}")
    print("  Fonte: Oracle. Pode ser diferente da simulação CSV local.")


def exportar_relatorio():
    dados = ler_dados()
    PASTA_RELATORIOS.mkdir(exist_ok=True)
    destino = PASTA_RELATORIOS / "resumo_energetico_por_dia.csv"
    resumo = dados.groupby("dia", as_index=False).agg(
        geracao_kwh=("geracao_kw", "sum"),
        consumo_kwh=("consumo_kw", "sum"),
        deficit_kwh=("deficit_kwh", "sum"),
        alertas=("alerta", "sum"),
    )
    resumo["saldo_kwh"] = resumo["geracao_kwh"] - resumo["consumo_kwh"]
    resumo.to_csv(destino, index=False, encoding="utf-8-sig", float_format="%.3f")
    print(f"\nRelatório exportado com sucesso: {destino}")


def mostrar_alertas():
    dados = ler_dados()
    alertas = dados.loc[dados["alerta"].astype(bool)]
    print("\n" + "=" * 65)
    print("  ALERTAS DA SIMULAÇÃO")
    print("=" * 65)
    print(f"  Total de intervalos em alerta: {len(alertas)} / {len(dados)}")
    if alertas.empty:
        print("  Não foram identificados alertas.")
        return
    resumo = alertas.groupby("dia", as_index=False).agg(
        quantidade=("alerta", "sum"),
        deficit_kwh=("deficit_kwh", "sum"),
    )
    for _, registro in resumo.iterrows():
        print(f"  Dia {int(registro['dia'])}: {int(registro['quantidade'])} alerta(s), "
              f"déficit {registro['deficit_kwh']:.2f} kWh")
    print("  Critério: bateria < 20% OU demanda não atendida.")


def menu_relatorios():
    acoes = {
        "1": resumo_energetico,
        "2": historico_oracle,
        "3": exportar_relatorio,
        "4": mostrar_alertas,
    }
    while True:
        print("\n" + "=" * 65)
        print("  RELATÓRIOS — AURORA SIGER")
        print("=" * 65)
        print("  1. Visualizar resumo energético (CSV)")
        print("  2. Consultar histórico de simulações (Oracle)")
        print("  3. Exportar resumo por dia (CSV)")
        print("  4. Visualizar alertas de sustentabilidade (CSV)")
        print("  0. Voltar")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "0":
            return
        if opcao not in acoes:
            print("Opção inválida. Digite um número de 0 a 4.")
            continue
        try:
            acoes[opcao]()
        except (ValueError, OSError) as erro:
            print(f"\nNão foi possível concluir: {erro}")
        input("\nPressione ENTER para voltar ao menu...")
