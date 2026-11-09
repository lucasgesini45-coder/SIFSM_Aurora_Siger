"""Interface de gestão de dados Oracle com operações CRUD por tipo de registro."""
from src import repositories as repo
from src.database import ErroBanco

TABELAS = {
    "1": ("Simulações", {
        "listar": repo.listar_simulacoes,
        "buscar": repo.buscar_simulacao,
        "inserir": repo.inserir_simulacao,
        "atualizar": repo.atualizar_simulacao,
        "excluir": repo.excluir_simulacao,
        "campos": ("nome", "data_inicio"),
        "editaveis": ("nome", "data_inicio", "semente", "status"),
    }),
    "2": ("Intervalos horários", {
        "listar": repo.listar_intervalos,
        "buscar": repo.buscar_intervalo,
        "inserir": repo.inserir_intervalo,
        "atualizar": repo.atualizar_intervalo,
        "excluir": repo.excluir_intervalo,
        "campos": ("numero_intervalo", "temperatura_c", "irradiancia_wm2",
                   "geracao_kwh", "consumo_kwh"),
        "editaveis": ("temperatura_c", "irradiancia_wm2", "geracao_kwh", "consumo_kwh"),
        "pai": "simulacao_id",
    }),
    "3": ("Resultados da regressão", {
        "listar": repo.listar_regressoes,
        "buscar": repo.buscar_regressao,
        "inserir": repo.inserir_regressao,
        "atualizar": repo.atualizar_regressao,
        "excluir": repo.excluir_regressao,
        "campos": ("variavel_x", "variavel_y", "coef_angular", "intercepto",
                   "r_quadrado", "n_observacoes"),
        "editaveis": ("variavel_x", "variavel_y", "coef_angular", "intercepto",
                      "r_quadrado", "n_observacoes"),
        "pai": "simulacao_id",
    }),
    "4": ("Recomendações da IA", {
        "listar": repo.listar_recomendacoes,
        "buscar": repo.buscar_recomendacao,
        "inserir": repo.inserir_recomendacao,
        "atualizar": repo.atualizar_recomendacao,
        "excluir": repo.excluir_recomendacao,
        "campos": ("modelo", "tipo", "texto"),
        "editaveis": ("modelo", "tipo", "texto"),
        "pai": "simulacao_id",
    }),
}


def _campo(nome):
    valor = input(f"  {nome}: ").strip()
    if not valor:
        raise ValueError(f"Informe {nome}.")
    return valor


def _mostrar(registros):
    if isinstance(registros, dict):
        registros = [registros]
    if not registros:
        print("  Nenhum registro encontrado.")
        return
    for item in registros:
        print("  " + " | ".join(f"{chave}={valor}" for chave, valor in item.items()))


def executar_acao(acao, definicao):
    pai = definicao.get("pai")
    if acao == "1":
        argumentos = {_pai: _campo(_pai) for _pai in [pai]} if pai else {}
        _mostrar(definicao["listar"](**argumentos))
    elif acao == "2":
        _mostrar(definicao["buscar"](_campo("id")))
    elif acao == "3":
        argumentos = {campo: _campo(campo) for campo in definicao["campos"]}
        if pai:
            argumentos[pai] = _campo(pai)
        identificador = definicao["inserir"](**argumentos)
        print(f"  Registro criado com ID {identificador}.")
    elif acao == "4":
        identificador = _campo("id")
        print("  Campos permitidos: " + ", ".join(definicao["editaveis"]))
        campo = _campo("campo para alterar")
        if campo not in definicao["editaveis"]:
            raise ValueError("Campo não permitido para este registro.")
        valor = _campo("novo valor")
        definicao["atualizar"](identificador, **{campo: valor})
        print("  Registro atualizado.")
    elif acao == "5":
        identificador = _campo("id")
        print("  Atenção: excluir uma simulação também exclui seus registros vinculados.")
        confirmacao = input(f"  Digite EXCLUIR {identificador} para confirmar: ").strip()
        if confirmacao != f"EXCLUIR {identificador}":
            print("  Exclusão cancelada.")
            return
        definicao["excluir"](identificador)
        print("  Registro excluído.")


def menu_gestao():
    while True:
        print("\n===== GESTÃO DE DADOS — ORACLE =====")
        for chave, (rotulo, _) in TABELAS.items():
            print(f"{chave}. {rotulo}")
        print("0. Voltar")
        escolha = input("Escolha a categoria: ").strip()
        if escolha == "0":
            return
        if escolha not in TABELAS:
            print("Categoria inválida.")
            continue
        rotulo, definicao = TABELAS[escolha]
        while True:
            print(f"\n===== {rotulo.upper()} =====")
            print("1. Listar   2. Buscar por ID   3. Cadastrar")
            print("4. Atualizar   5. Excluir   0. Voltar")
            opcao = input("Escolha: ").strip()
            if opcao == "0":
                break
            if opcao not in {"1", "2", "3", "4", "5"}:
                print("Opção inválida.")
                continue
            try:
                executar_acao(opcao, definicao)
            except (ErroBanco, ValueError, TypeError, OSError) as erro:
                print(f"  Não foi possível concluir: {erro}")
            input("Pressione ENTER para continuar...")
