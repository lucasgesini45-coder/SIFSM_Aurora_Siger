# antes de iniciar a ia, é bom ressaltar que ela não é um chatbot convencional, ela é como se fosse uma linha de montagem e que cada peça é uma função
import os

import oracledb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

oracledb.defaults.fetch_lobs = False

# login como variavel de ambiente, senhas e users nao ficam diretamente no codigo
usuario = os.environ.get("ORACLE_USER", "(USUARIO_ORACLE)")
senha = os.environ.get("ORACLE_PASSWORD", "(SENHA_ORACLE)")
dsn = os.environ.get("ORACLE_DSN", "(HOST:PORTA/SERVICO)")
modelo_ia = "sifsm-triador-tfidf-logreg"
limite_irradiancia = 200.0  # (CONFIRMAR: irradiância média diária, em W/m², abaixo da qual o dia é nublado) -> comparar com os dados gerais
limiar_confianca = 0.60  # abaixo disso o triador chama um humano, a ia nao pode continuar executando se estiver abaixo disso

# ve o contexto da conversa
sessao = {"historico": [], "trace": [], "sim": None, "dia": None, "dia_foco": None}


# tira acentos dos textos para evitar erros de leitura
def sem_acento(texto):
    return texto.lower().translate(str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc"))


# texto de user nao entra no code para evitar problemas de seguranca
def rodar_sql(sql, parametros=None, escrever=False):
    """SELECT devolve lista de dicionários. INSERT só faz commit se não houve erro (else)."""
    conn = None
    try:
        conn = oracledb.connect(user=usuario, password=senha, dsn=dsn)
        cursor = conn.cursor()
        cursor.execute(sql, parametros or {})
        if not escrever:
            colunas = [
                c[0].lower() for c in cursor.description
            ]  # Oracle devolve MAIÚSCULAS
            linhas = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    except oracledb.Error as erro:
        raise ValueError("Erro no banco Oracle: " + str(erro))
    else:
        if escrever:
            conn.commit()
            return []
        return linhas
    finally:
        if conn:
            conn.close()  # sempre fecha (evitar deixar db aberto para nao sobrecarregar o sistema)


# ferramentas de consulta fixa da ia, as perguntas vem do db
def simulacao_atual():
    linhas = rodar_sql("SELECT id, nome, status FROM simulacao ORDER BY id DESC")
    if not linhas:
        raise ValueError(
            "Nenhuma simulação no banco. Rode o banco_aurora_siger.sql primeiro."
        )
    return linhas[0]


# faz um resulmo diario
def resumo_diario():
    dias = rodar_sql(
        "SELECT dia, SUM(geracao_kwh) AS geracao, SUM(consumo_kwh) AS consumo, SUM(saldo_kwh) AS saldo, "
        "AVG(irradiancia_wm2) AS irradiancia, AVG(temperatura_c) AS temperatura "
        "FROM intervalo_horario WHERE simulacao_id = :sim GROUP BY dia ORDER BY dia",
        {"sim": sessao["sim"]["id"]},
    )
    for d in dias:
        for campo in d:
            d[campo] = float(d[campo])  # número normal do Python
        d["dia"] = int(d["dia"])
    return dias


def regra_alerta(deficit, irradiancia_baixa):
    return (
        deficit and irradiancia_baixa
    )  # alerta = consumo > geração e dia com pouco sol


# RAG simulado
documentos = [  # (SUBSTITUIR pelos protocolos reais da Aurora Siger)
    "Quando o consumo diario supera a geracao e a irradiancia esta baixa, o sistema emite alerta e exige revisao humana.",
    "O pico de consumo ocorre entre 18h e 22h, quando nao ha geracao solar.",
    "A geracao solar e proporcional a irradiancia: a regressao registrada no banco descreve essa relacao.",
    "Dias com baixa irradiancia indicam nebulosidade e reduzem a geracao de energia.",
]
vet_docs = TfidfVectorizer()
mat_docs = vet_docs.fit_transform(documentos)


def buscar_documento(pergunta):
    sim = cosine_similarity(vet_docs.transform([sem_acento(pergunta)]), mat_docs)[0]
    return documentos[sim.argmax()] if sim.max() > 0.15 else None


# triator
exemplos = [  # aumentar frases
    ("qual o saldo de energia da semana", "energia"),
    ("quanta energia foi gerada", "energia"),
    ("qual o consumo total", "energia"),
    ("existe deficit de energia", "energia"),
    ("qual o saldo do dia 3", "energia"),
    ("como esta a irradiancia solar", "ambiental"),
    ("qual a temperatura media", "ambiental"),
    ("quais dias estao nublados", "ambiental"),
    ("e a temperatura nesse dia", "ambiental"),
    ("qual dia teve menos sol", "ambiental"),
    ("mostre os resultados da regressao", "dados"),
    ("qual o r quadrado do modelo", "dados"),
    ("quantos intervalos tem a simulacao", "dados"),
    ("qual o status da simulacao", "dados"),
    ("qual a receita de bolo", "fora_do_escopo"),
    ("quem ganhou o jogo ontem", "fora_do_escopo"),
    ("conte uma piada", "fora_do_escopo"),
    ("qual a capital da franca", "fora_do_escopo"),
]
vetorizador = TfidfVectorizer()
classificador = LogisticRegression(C=20, max_iter=1000)
classificador.fit(
    vetorizador.fit_transform([sem_acento(f) for f, area in exemplos]),
    [area for f, area in exemplos],
)


def triar(pergunta):
    """Retorna (área, confiança de 0 a 1)."""
    probs = classificador.predict_proba(vetorizador.transform([sem_acento(pergunta)]))[
        0
    ]
    return classificador.classes_[probs.argmax()], probs.max()


# ---------------------------------------------------------------------
# 5. agentes: cada um devolve (texto, próximo_agente). Próximo agente = HANDOFF.
# ---------------------------------------------------------------------
def agente_energia(pergunta):
    dias = resumo_diario()
    dia = sessao["dia"]  # contexto: dia citado antes
    escolhidos = [d for d in dias if d["dia"] == dia] if dia else dias
    if not escolhidos:
        return "Não encontrei dados para esse dia na simulação.", None
    geracao = sum(d["geracao"] for d in escolhidos)
    consumo = sum(d["consumo"] for d in escolhidos)
    rotulo = f"Dia {dia}" if dia else f"Semana ({len(dias)} dias)"
    texto = f"{rotulo}: geração {geracao:.1f} kWh, consumo {consumo:.1f} kWh, saldo {geracao - consumo:+.1f} kWh."

    alertas = [
        d
        for d in escolhidos
        if regra_alerta(
            d["consumo"] > d["geracao"], d["irradiancia"] < limite_irradiancia
        )
    ]
    if alertas:
        pior = alertas[0]
        for d in alertas:
            if d["saldo"] < pior["saldo"]:
                pior = d
        sessao["dia_foco"] = pior["dia"]
        texto += (
            f" ALERTA: déficit com baixa irradiância no(s) dia(s) {', '.join(str(d['dia']) for d in alertas)}."
            " RECOMENDAÇÃO: reduzir o consumo (principalmente 18h-22h) ou ampliar a geração."
        )
        return texto, "ambiental"  # HANDOFF: o ambiental explica a causa
    return texto, None


def agente_ambiental(pergunta):
    dias = resumo_diario()
    dia = sessao["dia"] or sessao["dia_foco"]  # dia da conversa ou vindo de um handoff
    sessao["dia_foco"] = None
    if dia:
        escolhidos = [d for d in dias if d["dia"] == dia]
        if not escolhidos:
            return "Não encontrei dados para esse dia na simulação.", None
        d = escolhidos[0]
        texto = (
            f"Dia {dia}: irradiância média {d['irradiancia']:.0f} W/m² (limite {limite_irradiancia:.0f}), "
            f"temperatura média {d['temperatura']:.1f} °C."
        )
        return (
            texto
            + (
                " Dia nublado: geração solar reduzida."
                if d["irradiancia"] < limite_irradiancia
                else ""
            ),
            None,
        )
    menor = dias[0]
    for d in dias:
        if d["irradiancia"] < menor["irradiancia"]:
            menor = d
    media = sum(d["temperatura"] for d in dias) / len(dias)
    return (
        f"Temperatura média da semana {media:.1f} °C. Dia com menos sol: dia {menor['dia']} ({menor['irradiancia']:.0f} W/m²).",
        None,
    )


def agente_dados(pergunta):
    sim = sessao["sim"]
    n = rodar_sql(
        "SELECT COUNT(*) AS n FROM intervalo_horario WHERE simulacao_id = :sim",
        {"sim": sim["id"]},
    )[0]["n"]
    texto = f"Simulação '{sim['nome']}' (status {sim['status']}) com {int(n)} intervalos horários."
    reg = rodar_sql(
        "SELECT variavel_x, variavel_y, coef_angular, intercepto, r_quadrado FROM regressao_resultado "
        "WHERE simulacao_id = :sim ORDER BY id DESC",
        {"sim": sim["id"]},
    )
    if reg:
        r = reg[0]
        return (
            texto
            + (
                f" Regressão: {r['variavel_y']} = {float(r['coef_angular']):.4f} · {r['variavel_x']} "
                f"+ {float(r['intercepto']):.4f} (R² = {float(r['r_quadrado']):.3f})."
            ),
            None,
        )
    return texto + " Nenhuma regressão registrada ainda.", None


agentes = {
    "energia": agente_energia,
    "ambiental": agente_ambiental,
    "dados": agente_dados,
}

# guardrails
proibido = [
    "desligar suporte de vida",
    "desativar alarme",
    "ignorar protocolo",
    "apagar o banco",
]
privado = ["dados pessoais", "historico medico", "saude do tripulante"]


def guardrail_entrada(pergunta):
    """Devolve a mensagem de bloqueio, ou None se a pergunta pode seguir."""
    texto = sem_acento(pergunta)
    if any(t in texto for t in proibido):
        return "Bloqueado: ação insegura. Exige autorização humana presencial."
    if any(t in texto for t in privado):
        return "Bloqueado: dados individuais da tripulação são protegidos."
    return None


def guardrail_saida(resposta):
    """O sistema só SUGERE: se disser que executou algo, a resposta é descartada."""
    if any(p in sem_acento(resposta) for p in ["executei", "desliguei", "desativei"]):
        return "Resposta descartada: o sistema não executa ações, apenas sugere."
    return (
        resposta + "\n  ℹ Sugestão automática: requer validação de um operador humano."
    )


def extrair_dia(pergunta):
    palavras = sem_acento(pergunta).replace("?", " ").split()
    for i in range(len(palavras) - 1):
        if palavras[i] == "dia" and palavras[i + 1].isdigit():
            return int(palavras[i + 1])
    return None


def gravar_resposta(resposta):
    tipo = (
        "ALERTA"
        if "ALERTA" in resposta
        else "RECOMENDACAO" if "RECOMENDAÇÃO" in resposta else "EXPLICACAO"
    )
    try:
        rodar_sql(
            "INSERT INTO recomendacao_ia (simulacao_id, modelo, tipo, texto) VALUES (:sim, :modelo, :tipo, :texto)",
            {
                "sim": sessao["sim"]["id"],
                "modelo": modelo_ia,
                "tipo": tipo,
                "texto": resposta,
            },
            escrever=True,
        )
        sessao["trace"].append(f"banco: gravado em recomendacao_ia ({tipo})")
    except ValueError as erro:
        sessao["trace"].append("banco: falha ao gravar - " + str(erro)[:50])


def atender(pergunta):
    sessao["historico"].append(("tripulante", pergunta))
    resposta = processar(pergunta)
    sessao["historico"].append(("sistema", resposta))
    return resposta


def processar(pergunta):
    bloqueio = guardrail_entrada(pergunta)  # 1) guardrail de entrada
    if bloqueio:
        sessao["trace"].append("guardrail: pergunta bloqueada")
        return bloqueio

    area, confianca = triar(pergunta)  # 2) triador (IA)
    sessao["trace"].append(f"triador: {area} ({confianca:.0%})")
    if area == "fora_do_escopo" or confianca < limiar_confianca:
        sessao["trace"].append("handoff: triador -> humano")
        return f"Não consigo atender com segurança ({area}, {confianca:.0%}). Encaminhado a um operador humano."

    sessao["sim"] = simulacao_atual()  # 3) contexto da sessão
    if extrair_dia(pergunta):
        sessao["dia"] = extrair_dia(pergunta)
    if "semana" in sem_acento(pergunta):
        sessao["dia"] = None

    respostas = []
    while area is not None:  # 4) agentes (segue os handoffs)
        texto, proximo = agentes[area](pergunta)
        respostas.append(f"[Agente {area}] {texto}")
        sessao["trace"].append(
            f"agente {area} respondeu" + (f" -> handoff: {proximo}" if proximo else "")
        )
        area = proximo

    documento = buscar_documento(pergunta)  # 5) RAG
    if documento:
        respostas.append("Base de conhecimento: " + documento)
    resposta = guardrail_saida("\n".join(respostas))  # 6) guardrail de saída
    gravar_resposta(resposta)  # 7) auditoria no Oracle
    return resposta


# ---------------------------------------------------------------------
# Interface de terminal: somente apresentação. Os cálculos e a IA não mudam.
# ---------------------------------------------------------------------
import re
import textwrap

LARGURA = 76


def linha():
    print("-" * LARGURA)


def titulo(texto):
    print()
    print("=" * LARGURA)
    print(f"  {texto.upper()}")
    print("=" * LARGURA)


def secao(texto):
    print()
    print(f"  {texto.upper()}")
    linha()


def mensagem(texto, recuo=2):
    """Quebra linhas longas sem cortar palavras, respeitando quebras existentes."""
    prefixo = " " * recuo
    for trecho in str(texto).splitlines():
        if not trecho.strip():
            print()
        else:
            print(textwrap.fill(
                trecho.strip(), width=LARGURA,
                initial_indent=prefixo, subsequent_indent=prefixo
            ))


def resposta_formatada(resposta):
    """Exibe a resposta original organizada por agente e categoria."""
    titulo("Resposta da inteligência artificial")
    for bloco in str(resposta).splitlines():
        parte = bloco.strip()
        if not parte:
            continue
        match = re.match(r"^\[Agente ([^\]]+)\]\s*(.*)$", parte)
        if match:
            secao("Agente " + match.group(1))
            parte = match.group(2)
        elif parte.startswith("Base de conhecimento:"):
            secao("Base de conhecimento — exemplo")
            parte = parte.split(":", 1)[1].strip()
        elif parte.startswith("ℹ"):
            secao("Validação humana")
            parte = parte.lstrip("ℹ ").strip()

        # Separar avisos das métricas, sem alterar os textos persistidos no Oracle.
        partes = re.split(r"\s+(?=(?:ALERTA|RECOMENDAÇÃO):)", parte)
        for item in partes:
            if item.startswith("ALERTA:"):
                secao("Atenção | Alerta")
                mensagem(item[len("ALERTA:"):].strip())
            elif item.startswith("RECOMENDAÇÃO:"):
                secao("Recomendação")
                mensagem(item[len("RECOMENDAÇÃO:"):].strip())
            else:
                mensagem(item)
    print()


def erro_amigavel(erro):
    titulo("Não foi possível concluir a operação")
    mensagem(str(erro))
    mensagem("Verifique a conexão Oracle e tente novamente.")
    print()


def aguardar():
    input("Pressione ENTER para voltar ao menu...")


def apresentar_papel():
    titulo("Papel, limites e segurança da IA")
    secoes = [
        ("Papel da IA",
         "Interpreta perguntas e seleciona um agente especialista e uma consulta "
         "pré-definida. Os números vêm do banco Oracle, não são inventados pela IA."),
        ("Limitações",
         "O triador foi treinado com poucos exemplos e pode errar. "
         "Perguntas com baixa confiança exigem revisão humana."),
        ("Segurança",
         "Guardrails impedem algumas ações inseguras e consultas a dados "
         "individuais. Nenhum texto livre de usuário é incorporado à consulta SQL."),
        ("Auditoria",
         "As respostas aceitas pelo fluxo são encaminhadas para registro em "
         "RECOMENDACAO_IA. Falhas na gravação ficam registradas no tracing."),
        ("Responsabilidade humana",
         "Os agentes apenas sugerem. Nenhuma recomendação se transforma "
         "automaticamente em ação na colônia.")
    ]
    for nome, texto in secoes:
        secao(nome)
        mensagem(texto)
    print()


# Webhook simulado: não realiza chamada externa ou notificação real.
def simular_webhook(tipo, dia):
    perguntas = {
        "deficit_energia": "qual o saldo de energia do dia ",
        "irradiancia_baixa": "como esta a irradiancia do dia ",
    }
    pergunta = perguntas[tipo] + str(dia)
    titulo("Webhook demonstrativo")
    secao("1. Evento recebido")
    mensagem(f"Tipo: {tipo} | Dia: {dia}")
    secao("2. Pergunta gerada")
    mensagem(pergunta)
    secao("3. Processamento por agentes")
    resposta_formatada(atender(pergunta))
    secao("4. Encaminhamento simulado")
    mensagem("Notificação ao operador humano: exemplo de fluxo e-mail/Slack. "
             "Nenhuma notificação externa foi enviada.")


def fazer_pergunta():
    titulo("Perguntar à IA")
    mensagem("Exemplos: 'qual o saldo de energia da semana?' "
             "ou 'como está a irradiância do dia 2?'")
    mensagem("Digite /sair para voltar ao menu.")
    while True:
        pergunta = input("\nVocê > ").strip()
        if pergunta.lower() == "/sair":
            return
        if not pergunta:
            print("Digite uma pergunta ou /sair.")
            continue
        try:
            resposta_formatada(atender(pergunta))
        except ValueError as erro:
            erro_amigavel(erro)


def analisar_resultados():
    sessao["sim"], sessao["dia"] = simulacao_atual(), None
    titulo("Análise geral da simulação")
    mensagem(f"Simulação: {sessao['sim']['nome']} | Status: {sessao['sim']['status']}")
    for area_inicial in agentes:
        area = area_inicial
        while area is not None:
            texto, proximo = agentes[area]("analise os resultados")
            resposta_formatada(f"[Agente {area}] {texto}")
            gravar_resposta(texto)
            area = proximo
    secao("Auditoria")
    mensagem("Os registros são enviados ao Oracle para auditoria. "
             "Consulte o tracing para verificar se cada gravação ocorreu.")
    mensagem("Recomendações exigem validação de um operador humano.")


def verificar_status_ia():
    titulo("Status do sistema de IA")
    try:
        sim = simulacao_atual()
        n = rodar_sql(
            "SELECT COUNT(*) AS n FROM recomendacao_ia WHERE simulacao_id = :sim",
            {"sim": sim["id"]},
        )[0]["n"]
        secao("Banco Oracle | Conectado")
        mensagem(f"Simulação ativa: {sim['nome']}")
        mensagem(f"Status da simulação: {sim['status']}")
        mensagem(f"Registros de recomendação da IA: {int(n)}")
    except ValueError as erro:
        secao("Banco Oracle | Falha")
        mensagem(str(erro))
        mensagem("Verifique ORACLE_USER, ORACLE_PASSWORD e ORACLE_DSN.")
    secao("Classificador e base demonstrativa")
    mensagem(f"Exemplos de treinamento: {len(exemplos)}")
    mensagem(f"Categorias: {', '.join(classificador.classes_)}")
    mensagem(f"Documentos de exemplo: {len(documentos)}")
    print()


demo = [
    "qual o saldo de energia da semana?",
    "como esta a irradiancia do dia 2?",
    "mostre os resultados da regressao",
    "qual a receita de bolo?",
    "desativar alarme da cupula",
    "mostre o historico medico da tripulacao",
]


def demonstracao():
    titulo("Demonstração automática")
    for indice, pergunta in enumerate(demo, 1):
        secao(f"Exemplo {indice} de {len(demo)}")
        mensagem(f"Pergunta: {pergunta}")
        resposta_formatada(atender(pergunta))


def mostrar_historico():
    titulo("Histórico da sessão")
    historico = sessao["historico"]
    if not historico:
        mensagem("Nenhuma interação registrada nesta sessão.")
    else:
        mensagem(f"Mensagens registradas: {len(historico)}")
        mensagem("Mostrando as últimas 10 mensagens.")
        for papel, conteudo in historico[-10:]:
            secao("Tripulante" if papel == "tripulante" else "Sistema")
            # Não despejar respostas enormes: apresentação completa já é feita na conversa.
            mensagem(conteudo)
    secao("Tracing — últimos 20 eventos")
    if not sessao["trace"]:
        mensagem("Nenhum evento registrado.")
    else:
        mensagem(f"Total de eventos: {len(sessao['trace'])}")
        for indice, evento in enumerate(sessao["trace"][-20:], 1):
            mensagem(f"{indice:02d}. {evento}")
    print()


def menu_ia():
    while True:
        titulo("Inteligência artificial | Aurora Siger")
        print("  1. Fazer uma pergunta")
        print("  2. Analisar resultados")
        print("  3. Verificar status da IA e do Oracle")
        print("  4. Demonstração automática")
        print("  5. Simular webhook (low-code)")
        print("  6. Histórico e tracing da sessão")
        print("  7. Papel, limites e segurança da IA")
        print("  0. Voltar ao menu principal")
        linha()
        opcao = input("Escolha uma opção: ").strip()
        if not opcao:
            print("Nenhuma opção informada. Escolha um número de 0 a 7.")
            continue
        if opcao == "0":
            return
        acoes = {
            "1": fazer_pergunta,
            "2": analisar_resultados,
            "3": verificar_status_ia,
            "4": demonstracao,
            "5": lambda: (
                simular_webhook("deficit_energia", 2),
                simular_webhook("irradiancia_baixa", 7)
            ),
            "6": mostrar_historico,
            "7": apresentar_papel,
        }
        acao = acoes.get(opcao)
        if not acao:
            print("Opção inválida. Escolha um número de 0 a 7.")
            continue
        try:
            acao()
        except ValueError as erro:
            erro_amigavel(erro)
        aguardar()


if __name__ == "__main__":
    menu_ia()
