"""Regra booleana do alerta energético do SIFSM Aurora Siger.

Entradas: A = consumo alto; B = módulo crítico; C = falha.
Saída: ALERTA = (A AND B) OR C.

Esta implementação é uma simulação de software independente do Arduino,
sem comunicação serial nem acionamento de equipamentos reais.
"""
from itertools import product


def avaliar_alerta(a: bool, b: bool, c: bool) -> bool:
    """Aplica a mesma expressão implementada no sketch do Arduino."""
    if not all(type(v) is bool for v in (a, b, c)):
        raise ValueError("As entradas A, B e C devem ser booleanas (True/False).")
    return (a and b) or c


def tabela_verdade():
    """As oito combinações de três entradas digitais."""
    return [
        {"A": a, "B": b, "C": c, "alerta": avaliar_alerta(a, b, c)}
        for a, b, c in product((False, True), repeat=3)
    ]


def _bit(valor):
    return "1" if valor else "0"


def exibir_tabela():
    print("\n" + "=" * 52)
    print("  TABELA VERDADE - SISTEMA DE ALERTA ENERGÉTICO")
    print("=" * 52)
    print("  A (consumo alto) | B (crítico) | C (falha) | ALERTA")
    print("  " + "-" * 50)
    for registro in tabela_verdade():
        print(f"         {_bit(registro['A'])}         |"
              f"      {_bit(registro['B'])}      |"
              f"     {_bit(registro['C'])}     |"
              f"   {_bit(registro['alerta'])}")
    print("\n  Expressão: ALERTA = (A AND B) OR C")
    print("  1 = verdadeiro / 0 = falso")


def _ler_entrada(rotulo):
    while True:
        entrada = input(f"  {rotulo} (1=sim, 0=não, 0/1): ").strip()
        if entrada in {"0", "1"}:
            return entrada == "1"
        print("  Entrada inválida: digite 1 ou 0.")


def simular_entrada():
    print("\n" + "=" * 52)
    print("  SIMULAÇÃO DE DECISÃO - PYTHON")
    print("=" * 52)
    a = _ler_entrada("A - consumo alto")
    b = _ler_entrada("B - módulo crítico")
    c = _ler_entrada("C - falha detectada")
    alerta = avaliar_alerta(a, b, c)
    print("\n  ENTRADAS")
    print(f"  A = {_bit(a)} | B = {_bit(b)} | C = {_bit(c)}")
    print("  REGRA: (A AND B) OR C")
    print(f"  SAÍDA: {'ALERTA ATIVO' if alerta else 'SEM ALERTA'}")
    if alerta:
        print("  Arduino (equivalência): LED aceso e buzzer ligado.")
    else:
        print("  Arduino (equivalência): LED apagado e buzzer desligado.")
    print("  Esta é uma simulação em Python; nenhum dispositivo físico foi acionado.")
    return alerta


def explicar_arquitetura():
    print("\n" + "=" * 64)
    print("  ARQUITETURA COMPUTACIONAL - EXEMPLO DE CONTROLE")
    print("=" * 64)
    print("  [1] Entrada: botões digitais A, B e C (Arduino/Tinkercad)")
    print("  [2] Controle local: CPU do Arduino executa (A AND B) OR C")
    print("  [3] Saída local: LED e buzzer indicam o estado do alerta")
    print("  [4] Python: demonstra a MESMA lógica, sem depender do Arduino")
    print("  [5] CSV/Oracle: armazenam dados da simulação energética")
    print("  [6] IA e regressão: analisam indicadores e orientam o operador")
    print("\n  IMPORTANTE: conexão serial Arduino -> Python não está implementada.")
    print("  GPU/NPU/TPU não são necessárias para essa decisão booleana.")
    print("  O controle local pode funcionar sem acesso ao banco ou à IA.")


def menu_alerta():
    while True:
        print("\n===== CIRCUITOS LÓGICOS E ARQUITETURA =====")
        print("1. Testar regra booleana em Python")
        print("2. Mostrar tabela verdade")
        print("3. Explicar integração Arduino, Python e Oracle")
        print("0. Voltar")
        opcao = input("Escolha uma opção: ").strip()
        if opcao == "0":
            return
        if opcao == "1":
            simular_entrada()
        elif opcao == "2":
            exibir_tabela()
        elif opcao == "3":
            explicar_arquitetura()
        else:
            print("Opção inválida. Tente novamente.")
        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    menu_alerta()
