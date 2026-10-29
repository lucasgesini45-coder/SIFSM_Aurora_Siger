
def menu_submenu(titulo, opcoes):
    while True:
        print(f"\n===== {titulo.upper()} =====")

        for codigo, descricao in opcoes.items():
            print(f"{codigo}. {descricao}")

        print("0. Voltar")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == "0":
            break

        if opcao in opcoes:
            print(f"\n{opcoes[opcao]}: funcionalidade em desenvolvimento.")
            input("Pressione ENTER para continuar...")
        else:
            print("Opção inválida.")


def main():
    while True:
        print("\n===== SIFSM AURORA SIGER =====")
        print("1. Gestão de dados")
        print("2. Simulação e análises")
        print("3. Inteligência artificial")
        print("4. Relatórios")
        print("5. Configurações")
        print("0. Sair")

        opcao = input("Escolha uma opção: ").strip()

        match opcao:
            case "1":
                menu_submenu("Gestão de dados", {
                    "1": "Cadastrar registro",
                    "2": "Consultar registros",
                    "3": "Atualizar registro",
                    "4": "Excluir registro",
                })

            case "2":
                menu_submenu("Simulação e análises", {
                    "1": "Executar simulação de 168 horas",
                    "2": "Consultar resultados",
                    "3": "Executar regressão",
                })

            case "3":
                menu_submenu("Inteligência artificial", {
                    "1": "Fazer uma pergunta",
                    "2": "Analisar resultados",
                    "3": "Verificar status da IA",
                })

            case "4":
                menu_submenu("Relatórios", {
                    "1": "Visualizar resumo",
                    "2": "Consultar histórico",
                    "3": "Exportar dados para CSV",
                })

            case "5":
                menu_submenu("Configurações", {
                    "1": "Verificar conexão Oracle",
                    "2": "Consultar configurações",
                    "3": "Informações do sistema",
                })

            case "0":
                print("Encerrando o SIFSM Aurora Siger...")
                break

            case _:
                print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
