"""
banco_aurora_siger.py  (Pessoa 1 - Banco de dados Oracle)

Faz tudo da parte do banco em um unico arquivo:
  1. verificar_conexao()  -> funcao exigida pelo projeto
  2. criar_banco()        -> executa banco_aurora_siger.sql no Oracle
  3. validar_banco()      -> confere tabelas, 168 intervalos e constraints

Requisitos:  pip install oracledb
Variaveis de ambiente:
  ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN   (ex.: localhost:1521/XEPDB1)

Uso:
  python banco_aurora_siger.py
"""

import os
import sys
from pathlib import Path

import oracledb

ARQUIVO_SQL = Path(__file__).with_name("banco_aurora_siger.sql")
TABELAS = {"SIMULACAO", "INTERVALO_HORARIO",
           "REGRESSAO_RESULTADO", "RECOMENDACAO_IA"}


# ---------------------------------------------------------------------
# Conexao
# ---------------------------------------------------------------------
def _conectar():
    return oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=os.getenv("ORACLE_DSN"),
    )


def verificar_conexao() -> bool:
    """True se conseguir conectar e executar uma consulta simples."""
    try:
        with _conectar() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM dual")
                return cur.fetchone()[0] == 1
    except oracledb.Error as e:
        print(f"[ERRO] Falha na conexao com o Oracle: {e}")
        return False


# ---------------------------------------------------------------------
# Execucao do script SQL
# ---------------------------------------------------------------------
def _separar_comandos(texto: str) -> list[str]:
    comandos, atual, em_bloco = [], [], False

    for linha in texto.splitlines():
        s = linha.strip()

        if "4. VALIDACAO" in s:         
            break
        if not atual and (not s or s.startswith("--")):
            continue
        if not atual and s.upper().split(" ")[0] in ("SET", "WHENEVER", "PROMPT"):
            continue

        if not atual and s.upper().startswith(("BEGIN", "DECLARE")):
            em_bloco = True

        if em_bloco:
            if s == "/":
                comandos.append("\n".join(atual))
                atual, em_bloco = [], False
            else:
                atual.append(linha)
        else:
            atual.append(linha)
            if s.endswith(";"):
                comandos.append("\n".join(atual).rstrip().rstrip(";"))
                atual = []

    return comandos


def criar_banco() -> bool:
    if not ARQUIVO_SQL.exists():
        print(f"[ERRO] Arquivo nao encontrado: {ARQUIVO_SQL}")
        return False

    comandos = _separar_comandos(ARQUIVO_SQL.read_text(encoding="utf-8"))
    try:
        with _conectar() as conn:
            with conn.cursor() as cur:
                for i, cmd in enumerate(comandos, 1):
                    try:
                        cur.execute(cmd)
                    except oracledb.Error as e:
                        conn.rollback()
                        print(f"[ERRO] Comando {i} falhou: {e}\n{cmd[:200]}...")
                        return False
            conn.commit()
        print(f"[OK] {len(comandos)} comandos executados.")
        return True
    except oracledb.Error as e:
        print(f"[ERRO] {e}")
        return False


# ---------------------------------------------------------------------
# Validacao
# ---------------------------------------------------------------------
def validar_banco() -> bool:
    """Confere se o banco esta correto. Retorna True se tudo passou."""
    ok = True

    def checar(descricao: str, condicao: bool):
        nonlocal ok
        print(f"[{'OK' if condicao else 'FALHA'}] {descricao}")
        ok = ok and condicao

    try:
        with _conectar() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM user_tables")
                existentes = {r[0] for r in cur}
                checar("4 tabelas criadas", TABELAS.issubset(existentes))

                cur.execute("SELECT COUNT(*) FROM intervalo_horario")
                checar("168 intervalos horarios", cur.fetchone()[0] == 168)

                cur.execute("""SELECT COUNT(*) FROM (
                                 SELECT dia FROM intervalo_horario
                                 GROUP BY dia HAVING COUNT(*) = 24)""")
                checar("7 dias com 24 intervalos cada", cur.fetchone()[0] == 7)

                cur.execute("""SELECT COUNT(*) FROM user_constraints
                               WHERE constraint_type = 'R'
                                 AND table_name IN ('INTERVALO_HORARIO',
                                     'REGRESSAO_RESULTADO','RECOMENDACAO_IA')""")
                checar("3 chaves estrangeiras", cur.fetchone()[0] == 3)

                # testa se a restricao de integridade realmente bloqueia
                try:
                    cur.execute("""INSERT INTO intervalo_horario
                        (simulacao_id, numero_intervalo, dia, hora, data_hora,
                         temperatura_c, irradiancia_wm2, geracao_kwh, consumo_kwh)
                        VALUES (-1, 1, 1, 0, SYSTIMESTAMP, 20, 0, 0, 0)""")
                    checar("FK bloqueia simulacao inexistente", False)
                except oracledb.IntegrityError:
                    checar("FK bloqueia simulacao inexistente", True)
            conn.rollback()
    except oracledb.Error as e:
        print(f"[ERRO] {e}")
        return False

    return ok


# ---------------------------------------------------------------------
if __name__ == "__main__":
    if not verificar_conexao():
        sys.exit("Sem conexao com o Oracle. Confira ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN.")
    print("[OK] Conexao com o Oracle")

    if not criar_banco():
        sys.exit(1)

    print("\n--- Validacao ---")
    sys.exit(0 if validar_banco() else 1)