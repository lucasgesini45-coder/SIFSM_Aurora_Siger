"""Diagnósticos de configuração sem exposição de senhas."""
import importlib.util
import os
import platform
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def verificar_oracle():
    """Usa a mesma configuração .env e a mesma conexão do CRUD."""
    from src.database import verificar_conexao

    print("\n===== CONEXÃO ORACLE =====")
    resultado = verificar_conexao()
    if resultado["conectado"]:
        print("  Status: CONECTADO")
        print("  Versão do banco:", resultado["versao"])
        print("  Usuário:", resultado["usuario"])
    else:
        print("  Status: FALHA")
        print("  Diagnóstico:", resultado["erro"])
    print("  A senha e o DSN não são exibidos.")



def consultar_configuracoes():
    print("\n===== CONFIGURAÇÕES =====")
    print("  Python:", sys.version.split()[0])
    print("  Sistema:", platform.system())
    print("  Pasta do projeto:", RAIZ)
    print("  Fonte da simulação: CSV local")
    print("  Fonte da IA: Oracle, quando configurado")
    from src.config import ErroConfiguracao, obter_config
    try:
        config = obter_config()
        print("  Oracle configurado: SIM (arquivo .env ou ambiente)")
        print("  Usuário configurado: SIM" if config.usuario else "  Usuário configurado: NÃO")
        print("  Senha configurada: SIM" if config.senha else "  Senha configurada: NÃO")
        print("  Serviço/DSN configurado: SIM" if config.dsn else "  Serviço/DSN configurado: NÃO")
    except ErroConfiguracao as erro:
        print("  Oracle configurado: NÃO")
        print("  Diagnóstico:", erro)
    print("  Senhas e valores de conexão são ocultados por segurança.")


def informacoes_sistema():
    print("\n===== SOBRE O SIFSM AURORA SIGER =====")
    print("  Sistema Integrado de Futuro Sustentável em Marte")
    print("  Protótipo acadêmico de simulação energética e análises")
    print("  Simulação: 168 horas, dados sintéticos")
    print("  IA: triador com agentes especializados e supervisão humana")
    print("  Nota: a opção 4 de Simulação grava explicitamente no Oracle.")


def verificar_modulos():
    print("\n===== INTEGRIDADE DOS MÓDULOS =====")
    arquivos = [
        "codigo_fonte.py", "src/simulation.py", "src/regression.py",
        "ia/ia_agentes.py", "banco_aurora_siger.sql", "requirements.txt",
        "src/config.py", "src/database.py", "src/repositories.py",
        "src/persistence_pipeline.py", "src/cli_data.py",
    ]
    for nome in arquivos:
        ok = (RAIZ / nome).is_file()
        print(f"  {'OK     ' if ok else 'AUSENTE'} {nome}")
    for nome in ("pandas", "numpy", "sklearn", "oracledb"):
        disponivel = importlib.util.find_spec(nome) is not None
        print(f"  {'OK     ' if disponivel else 'AUSENTE'} Biblioteca: {nome}")
    print("  Verificação estrutural: não substitui testes de execução.")


def menu_configuracoes():
    acoes = {
        "1": verificar_oracle,
        "2": consultar_configuracoes,
        "3": informacoes_sistema,
        "4": verificar_modulos,
    }
    while True:
        print("\n" + "=" * 65)
        print("  CONFIGURAÇÕES — AURORA SIGER")
        print("=" * 65)
        print("  1. Verificar conexão Oracle")
        print("  2. Consultar configurações")
        print("  3. Informações do sistema")
        print("  4. Verificar integridade dos módulos")
        print("  0. Voltar")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "0":
            return
        if opcao not in acoes:
            print("Opção inválida. Digite um número de 0 a 4.")
            continue
        acoes[opcao]()
        input("\nPressione ENTER para voltar ao menu...")
