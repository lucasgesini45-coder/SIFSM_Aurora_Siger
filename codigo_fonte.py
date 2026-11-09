"""Menu principal do SIFSM Aurora Siger."""
from pathlib import Path

ARQUIVO_CSV = Path(__file__).resolve().parent / "dados_aurora_siger.csv"


def pausar():
    input("\nPressione ENTER para continuar...")


def menu_submenu(titulo, opcoes):
    """Menu para funcionalidades ainda não implementadas."""
    while True:
        print(f"\n===== {titulo.upper()} =====")
        for codigo, descricao in opcoes.items():
            print(f"{codigo}. {descricao}")
        print("0. Voltar")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "0":
            return
        if opcao in opcoes:
            print(f"\n{opcoes[opcao]}: funcionalidade em desenvolvimento.")
            pausar()
        else:
            print("Opção inválida.")


def carregar_dados():
    import pandas as pd

    if not ARQUIVO_CSV.is_file() or ARQUIVO_CSV.stat().st_size == 0:
        raise FileNotFoundError("CSV ausente ou vazio. Execute primeiro a simulação.")
    return pd.read_csv(ARQUIVO_CSV)


def menu_simulacao():
    from src.simulation import gerar_simulacao, exportar_csv
    from src.regression import calcular_regressao
    from src.terminal_views import menu_csv, mostrar_regressao, resumo_csv

    while True:
        print("\n===== SIMULAÇÃO E ANÁLISES =====")
        print("1. Executar simulação de 168 horas")
        print("2. Consultar resultados do CSV")
        print("3. Executar regressão linear")
        print("4. Executar simulação e salvar no Oracle com regressão")
        print("0. Voltar")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "0":
            return
        try:
            if opcao == "1":
                dados = gerar_simulacao(168)
                exportar_csv(dados, ARQUIVO_CSV)
                print(f"CSV gerado: {ARQUIVO_CSV.name}")
                resumo_csv(dados)
                print("Consulte a opção 2 para visualizar os registros em páginas.")
            elif opcao == "2":
                dados = carregar_dados()
                menu_csv(dados)
            elif opcao == "3":
                dados = carregar_dados()
                resultado = calcular_regressao(dados)
                mostrar_regressao(resultado)
            elif opcao == "4":
                from datetime import date
                from src.persistence_pipeline import persistir_simulacao
                nome = input("Nome único da simulação no Oracle: ").strip()
                if not nome:
                    raise ValueError("Informe um nome para a simulação.")
                inicio_texto = input("Data inicial (AAAA-MM-DD, ENTER para hoje): ").strip()
                inicio = date.fromisoformat(inicio_texto) if inicio_texto else date.today()
                dados = gerar_simulacao(168)
                resultado = persistir_simulacao(dados, nome, data_inicio=inicio)
                print(f"Simulação #{resultado['simulacao_id']} e regressão "
                      f"#{resultado['regressao_id']} gravadas no Oracle.")
                print(f"Intervalos: {resultado['intervalos']}")
                print(f"R² do treinamento gravado no Oracle: {resultado['r2_treino_oracle']:.4f}")
                print(f"R² de teste temporal (somente relatório local): {resultado['r2_teste_local']}")
                resumo_csv(dados)
                try:
                    exportar_csv(dados, ARQUIVO_CSV)
                    print(f"CSV local atualizado: {ARQUIVO_CSV.name}")
                except OSError as erro:
                    print(f"Oracle gravado; não foi possível exportar o CSV local: {erro}")
            else:
                print("Opção inválida.")
                continue
        except (FileNotFoundError, ValueError, OSError) as erro:
            print(f"Falha: {erro}")
        except Exception as erro:
            from src.database import ErroBanco
            if not isinstance(erro, ErroBanco):
                raise
            print(f"Falha na persistência Oracle: {erro}")
        pausar()


def abrir_ia():
    try:
        from ia.ia_agentes import menu_ia
    except ImportError as erro:
        print(f"Não foi possível carregar a IA: {erro}")
        print("Confira se instalou as dependências de requirements.txt.")
        pausar()
        return
    menu_ia()


def main():
    while True:
        print("\n===== SIFSM AURORA SIGER =====")
        print("1. Gestão de dados")
        print("2. Simulação e análises")
        print("3. Inteligência artificial")
        print("4. Relatórios")
        print("5. Configurações")
        print("6. Circuitos lógicos e arquitetura")
        print("0. Sair")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "1":
            from src.cli_data import menu_gestao
            menu_gestao()
        elif opcao == "2":
            menu_simulacao()
        elif opcao == "3":
            abrir_ia()
        elif opcao == "4":
            from src.reports import menu_relatorios
            menu_relatorios()
        elif opcao == "5":
            from src.system_status import menu_configuracoes
            menu_configuracoes()
        elif opcao == "6":
            from src.logic_circuit import menu_alerta
            menu_alerta()
        elif opcao == "0":
            print("Encerrando o SIFSM Aurora Siger...")
            return
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
