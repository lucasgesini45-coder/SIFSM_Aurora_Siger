"""Diagnósticos de configuração sem exposição de senhas."""
import importlib.util
import os
import platform
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def verificar_oracle():
    print("\n===== CONEXÃO ORACLE =====")
    campos = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
    ausentes = [campo for campo in campos if not os.environ.get(campo)]
    if ausentes:
        print("  Não configurado neste terminal.")
        print("  Variáveis ausentes:", ", ".join(ausentes))
        return
    try:
        import oracledb
        with oracledb.connect(
            user=os.environ["ORACLE_USER"],
            password=os.environ["ORACLE_PASSWORD"],
            dsn=os.environ["ORACLE_DSN"],
        ) as conexao:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT 1 FROM dual")
                cursor.fetchone()
            print("  Status: CONECTADO")
            print("  Versão do banco:", conexao.version)
            print("  Usuário:", os.environ["ORACLE_USER"])
            # O endereço e a senha não são exibidos.
    except Exception as erro:
        print("  Falha ao conectar:", type(erro).__name__)
        print("  Verifique a rede, as credenciais e o serviço Oracle.")


def consultar_configuracoes():
    print("\n===== CONFIGURAÇÕES =====")
    print("  Python:", sys.version.split()[0])
    print("  Sistema:", platform.system())
    print("  Pasta do projeto:", RAIZ)
    print("  Fonte da simulação: CSV local")
    print("  Fonte da IA: Oracle, quando configurado")
    print("  Oracle user configurado:", "SIM" if os.environ.get("ORACLE_USER") else "NÃO")
    print("  Oracle senha configurada:", "SIM" if os.environ.get("ORACLE_PASSWORD") else "NÃO")
    print("  Oracle DSN configurado:", "SIM" if os.environ.get("ORACLE_DSN") else "NÃO")
    print("  Senhas e valores de conexão são ocultados por segurança.")


def informacoes_sistema():
    print("\n===== SOBRE O SIFSM AURORA SIGER =====")
    print("  Sistema Integrado de Futuro Sustentável em Marte")
    print("  Protótipo acadêmico de simulação energética e análises")
    print("  Simulação: 168 horas, dados sintéticos")
    print("  IA: triador com agentes especializados e supervisão humana")
    print("  Nota: o CSV da simulação não é gravado no Oracle automaticamente.")


def verificar_modulos():
    print("\n===== INTEGRIDADE DOS MÓDULOS =====")
    arquivos = [
        "codigo_fonte.py", "src/simulation.py", "src/regression.py",
        "ia/ia_agentes.py", "banco_aurora_siger.sql", "requirements.txt",
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
