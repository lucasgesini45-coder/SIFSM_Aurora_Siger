# SIFSM — Aurora Siger

**Sistema Integrado de Futuro Sustentável em Marte**  
**Atividade Integradora | Protótipo acadêmico | 2026**

> **Estado do projeto:** em desenvolvimento. O repositório já reúne menu em Python, simulação energética, regressão linear, script SQL e agentes de IA. Nem todos os requisitos da atividade estão concluídos. Este README descreve o que foi implementado, o que é demonstrativo e o que falta validar, sem confundir propostas com funcionalidades prontas.

## 1. Visão geral

O **SIFSM Aurora Siger** é um protótipo destinado a organizar dados operacionais de uma colônia fictícia em Marte e apoiar decisões sustentáveis por meio de simulação computacional, regras lógicas, análise estatística, estruturas de dados, banco de dados e agentes de inteligência artificial.

A aplicação é executada principalmente em um **menu de terminal Python**. Seu cenário inicial é a **gestão energética**, com geração solar simulada, demanda, bateria e alertas de operação. O sistema foi projetado para evoluir e integrar dados de outros módulos da colônia.

**Objetivos:**
- organizar registros e indicadores de operação e sustentabilidade;
- simular cenários e identificar condições de consumo, déficit e armazenamento;
- estimar tendências com um modelo linear e explicitar suas limitações;
- consultar informações por meio de agentes especializados, com limites de segurança;
- documentar decisões de arquitetura, impacto socioambiental e responsabilidade humana.

**Escopo acadêmico:** os números são sintéticos e as hipóteses são didáticas. O protótipo **não** controla equipamentos reais nem substitui operadores humanos. Sensores, circuitos, webhooks e automações podem ser apresentados por simulação ou representação conceitual, conforme o enunciado.

## 2. Estado atual e rastreabilidade dos requisitos

Legenda: **Implementado** = código presente e conectado ao fluxo descrito; **Parcial** = existe código ou documento, mas falta integração/validação; **Pendente** = ainda precisa ser desenvolvido e demonstrado. A classificação não significa que todos os testes foram executados com sucesso.

| Requisito da atividade | Situação | Evidência no repositório / próximo passo |
| --- | --- | --- |
| Código Python organizado e menu | **Implementado** | \`codigo_fonte.py\`; opções 1 a 5 |
| Dados estruturados | **Implementado** | \`dados_aurora_siger.csv\`, gerado pela simulação |
| Tabelas e banco Oracle | **Parcial** | \`banco_aurora_siger.sql\` define o esquema; implantação e credenciais da equipe não confirmadas |
| CRUD (cadastrar, listar, alterar, excluir) | **Pendente** | Menu de gestão exibe opções, mas ainda não executa CRUD |
| Tratamento de erros | **Implementado/parcial** | Validações em simulação/regressão e tratamento de falhas no código; testar fluxo completo |
| Regra booleana sustentável | **Parcial** | Alertas por bateria baixa/déficit na simulação; formalizar expressão e tabela-verdade |
| Circuito lógico, sensor ou automação representada | **Pendente** | Criar diagrama, Tinkercad ou descrição consistente com a regra escolhida |
| Estruturas de dados justificadas | **Parcial** | DataFrames, listas e dicionários presentes; documentar casos e escolhas, e demonstrar aplicação operacional |
| Simulação e conceitos matemáticos | **Implementado** | \`src/simulation.py\`; balanço energético e evolução da bateria em 168 intervalos |
| Modelo linear e avaliação | **Implementado** | \`src/regression.py\`; coeficientes, MAE, RMSE, R² de teste |
| Multiagentes, handoffs, guardrails e sessão | **Parcial** | \`ia/ia_agentes.py\` implementa fluxos; consultas reais dependem do Oracle |
| RAG / webhook / low-code | **Parcial** | Busca textual em documentos de exemplo e webhook simulado, não serviço externo real |
| Arquitetura CPU, GPU, memória e eficiência | **Pendente** | Redigir seção técnica vinculada aos componentes efetivamente usados |
| Sustentabilidade e cidadania digital | **Pendente** | Consolidar análise crítica no relatório técnico, com ao menos quatro pontos exigidos |
| Análise final de resultados e limitações | **Parcial** | Métricas disponíveis; falta consolidar visão integrada e relatório final |
| Vídeo de no máximo 5 minutos | **Pendente** | Gravar, publicar no YouTube como **Não listado** e preencher \`link_video.txt\` |
| ZIP completo para entrega | **Pendente** | Conferir os arquivos na seção 11 e compactar |

> A lista acima é um **checklist de acompanhamento**, não um atestado de aprovação. Atualizá-la quando cada integrante entregar novos módulos e os testes correspondentes.

## 3. Tecnologias e dependências

| Tecnologia | Utilização |
| --- | --- |
| Python | Menus, validação, integração e regras de negócio |
| NumPy | Cálculos numéricos e geração reproduzível da simulação |
| pandas | Tabelas de dados, leitura e exportação de CSV |
| scikit-learn | Classificação de perguntas e similaridade textual nos agentes |
| python-oracledb | Conexão e consultas ao Oracle |
| Oracle Database | Persistência proposta para simulações e recomendações da IA |
| unittest / pytest | Testes de validação e comportamento |

A atividade permite essas tecnologias quando coerentes com a proposta. A solução não depende de hardware físico, dashboard web ou API externa para demonstrar a simulação local.

## 4. Arquitetura e fluxo de dados

\`\`\`text
                  codigo_fonte.py (menu principal)
                              |
        +---------------------+---------------------+
        |                                           |
 Simulação e análises                         Inteligência artificial
 (src/simulation.py)                          (ia/ia_agentes.py)
        |                                           |
  168 intervalos, bateria,                  Triador de perguntas
  energia e alertas                          e agentes especializados
        |                                           |
  dados_aurora_siger.csv                     Consultas SQL fixas
        |                                           |
  src/regression.py                        Oracle Database
  coeficientes e métricas                  (se configurado)
\`\`\`

**Limite importante da integração:** esses **dois fluxos ainda não compartilham automaticamente os mesmos dados**. O simulador trabalha em CSV; a IA consulta registros Oracle. Não afirmar no vídeo que a simulação grava seus resultados no banco até que essa integração seja implementada e testada.

### 4.1 Arquivos principais

\`\`\`text
SIFSM_Aurora_Siger/
├── README.md
├── codigo_fonte.py
├── banco_aurora_siger.sql
├── dados_aurora_siger.csv
├── requirements.txt
├── relatorio_tecnico.md
├── link_video.txt
├── ia/
│   └── ia_agentes.py
├── src/
│   ├── __init__.py
│   ├── simulation.py
│   ├── regression.py
│   ├── services.py
│   ├── database.py
│   ├── repositories.py
│   ├── config.py
│   └── ai_assistant.py
├── tests/
│   ├── test_modulos.py
│   └── test_simulation.py
└── docs/
    ├── README_Pessoa3.md
    └── ANALISE_Pessoa3.md
\`\`\`

Alguns arquivos de suporte em \`src/\` permanecem sem implementação completa; não devem ser confundidos com funcionalidades já demonstráveis.

## 5. Instalação (Windows / VS Code)

**Recomendação de ambiente:** Python 3.11 ou 3.12. Confirme a versão instalada:

\`\`\`powershell
python --version
\`\`\`

Clone o repositório ou atualize sua cópia:

\`\`\`powershell
git clone https://github.com/lucasgesini45-coder/SIFSM_Aurora_Siger.git
cd SIFSM_Aurora_Siger
\`\`\`

Se o projeto já estiver na máquina, abra sua pasta e utilize \`git pull origin main\` em vez de clonar novamente.

Crie o ambiente virtual e instale as dependências:

\`\`\`powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install pytest
\`\`\`

O \`pytest\` é necessário para \`tests/test_simulation.py\` e ainda é instalado à parte no estado atual das dependências.

**Se o PowerShell bloquear a ativação**, execute os comandos com \`.\.venv\Scripts\python.exe\`, sem ativar o ambiente.

### 5.1 Iniciar o sistema

\`\`\`powershell
python codigo_fonte.py
\`\`\`

O menu possui:
1. **Gestão de dados** — opções de CRUD ainda demonstrativas;
2. **Simulação e análises** — simular, consultar CSV e executar regressão;
3. **Inteligência artificial** — menu de perguntas, análises, status e demonstrações;
4. **Relatórios** — funcionalidades pendentes;
5. **Configurações** — funcionalidades pendentes;
0. **Sair**.

## 6. Demonstração da simulação energética

No menu principal, selecione **2 → 1** para gerar **168 intervalos horários**, equivalentes a 7 dias convencionais de 24 horas. O sistema exporta \`dados_aurora_siger.csv\`; gerar novamente **sobrescreve** esse arquivo.

Depois use **2 → 2** para consultar os últimos registros e **2 → 3** para executar a regressão linear.

Também é possível executar diretamente:

\`\`\`powershell
python -m src.simulation
python -m src.regression
\`\`\`

### 6.1 Variáveis simuladas

O conjunto inclui hora, dia, geração e consumo de energia, condições de tempestade fictícia, energia inicial e final da bateria, estado de carga, carga/descarga, perdas, excedente, déficit e alerta.

Premissas principais já documentadas no código:
- 7 dias, 24 registros horários por dia, com semente aleatória fixa 42;
- consumo com componente base, aumento diurno e variação aleatória;
- geração solar no período diurno, reduzida nos dias 4 e 5 por tempestade simulada;
- bateria fictícia de 300 kWh, inicialmente com 240 kWh, eficiência de 95% na carga e descarga;
- alerta quando a carga final da bateria fica abaixo de 20% **ou** há déficit energético.

O balanço energético considera geração, consumo, armazenamento, perdas, excedente e déficit. Cada intervalo dura uma hora: por isso, o valor numérico da potência média em kW coincide com a energia do intervalo em kWh, mas **as unidades são diferentes**.

As hipóteses são **didáticas**. Consulte [a documentação específica da simulação](docs/README_Pessoa3.md) para fórmulas, dicionário de dados, limitações e interpretação.

### 6.2 Regra booleana e circuito — documentação em construção

Uma regra **já existente no simulador** é:

\`\`\`python
alerta = (energia_final_kwh < 0.20 * capacidade_kwh) or (deficit_kwh > 1e-9)
\`\`\`

Equação booleana correspondente: **A = B ∨ D**, em que **B** significa bateria abaixo de 20% e **D** significa déficit de energia. O circuito equivalente é uma **porta OR** com duas entradas e uma saída de alerta.

| Bateria abaixo de 20% (B) | Déficit (D) | Alerta (A) |
| --- | --- | --- |
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 1 |

Essa tabela representa a lógica do software. **Ainda falta** criar e anexar, se escolhida pela equipe, a representação visual do circuito (\`circuito_logico.png\`, \`circuito_logico.pdf\` ou \`link_tinkercad.txt\`). Não há evidência de Arduino físico implementado.

## 7. Modelo linear e interpretação

A regressão de \`src/regression.py\` ajusta uma relação didática entre **hora** (variável independente) e **consumo_kw** (variável dependente):

\`\`\`text
consumo_kw estimado = a × hora + b
\`\`\`

O código usa os primeiros 80% dos registros para treinamento e os últimos 20% para avaliação temporal, apresentando:
- coeficiente angular (\`a\`) e intercepto (\`b\`);
- MAE, RMSE e R² no conjunto de teste;
- MAE de uma referência simples, baseada na média do treino;
- estimativa ilustrativa para a próxima hora.

O coeficiente angular descreve a tendência linear média em relação ao índice horário; o intercepto é o valor estimado em hora zero. **Não interpretar o resultado como previsão operacional validada:** o índice de horas sozinho não descreve os ciclos de consumo ao longo do dia, e o R² pode ser negativo ou não definido. O modelo também não equivale à regressão de **irradiância versus geração** registrada como exemplo no SQL.

## 8. Oracle e integração da IA

O arquivo \`banco_aurora_siger.sql\` contém a criação e os dados de exemplo de quatro tabelas:

| Tabela | Função |
| --- | --- |
| \`SIMULACAO\` | Identificação, período e status da simulação |
| \`INTERVALO_HORARIO\` | Geração, consumo, saldo, irradiância e temperatura por intervalo |
| \`REGRESSAO_RESULTADO\` | Parâmetros e métricas da regressão vinculados à simulação |
| \`RECOMENDACAO_IA\` | Recomendações e alertas gerados pelos agentes |

**Status:** o arquivo SQL está no GitHub, mas **não está confirmado** que o integrante responsável tenha criado ou disponibilizado o banco Oracle. Antes da configuração, solicitar host, porta, nome do serviço, usuário e autorização de acesso. A senha deve ser enviada por um canal seguro, não em commit ou mensagem pública.

**Atenção:** o script SQL contém instruções que **removem e recriam** tabelas. Executá-lo pode apagar dados existentes; utilizar somente em ambiente autorizado de desenvolvimento após avaliação do responsável.

Se o banco estiver preparado, o módulo \`ia/ia_agentes.py\` usa as variáveis de ambiente:

\`\`\`powershell
$env:ORACLE_USER = "USUARIO_DA_APLICACAO"
$env:ORACLE_DSN = "HOST:1521/NOME_DO_SERVICO"
$cred = Get-Credential -UserName $env:ORACLE_USER
$env:ORACLE_PASSWORD = $cred.GetNetworkCredential().Password
\`\`\`

A senha não aparece nesses exemplos nem deve ser salva no repositório. Inicie \`python codigo_fonte.py\` e escolha **3 → 3** para verificar o status da IA e a conexão. A execução depende do banco acessível, do esquema e dos registros existentes.

### 8.1 Agentes e segurança

O código existente contém:
- **Triador** por TF-IDF e regressão logística para classificar perguntas;
- **Agente de energia**, **agente ambiental** e **agente de dados**;
- **Handoff** entre agentes conforme a análise;
- **Guardrails** para bloquear determinados assuntos e ações inseguras;
- **Sessão e tracing** do fluxo de atendimento;
- **Busca em documentos de exemplo** (RAG simplificado, não base documental completa);
- **Webhook simulado** e geração de recomendações para revisão humana.

A IA usa funções com consultas SQL predefinidas para buscar números no Oracle. O classificador foi treinado em poucas frases e pode errar; respostas, bloqueios e recomendações precisam de validação humana. A simulação de webhook **não** configura integração externa real.

**Integração ainda necessária:** estabelecer um contrato de campos/unidades entre os resultados da simulação CSV e as tabelas Oracle, implementar gravação transacional e validar leituras da IA sobre os mesmos dados produzidos pela simulação.

### 8.2 Apresentação no terminal

O submenu de inteligência artificial apresenta as opções em lista vertical, separa respostas por agente, destaca alertas, recomendações e validação humana. O status do Oracle e o tracing da sessão são mostrados em seções para facilitar a demonstração do projeto.

Após cada operação, o sistema solicita **ENTER para voltar ao menu**; opções vazias não executam ações. O histórico mostra as últimas dez mensagens e os últimos vinte eventos de tracing, mantendo o histórico em memória para a sessão atual. Os textos persistidos no Oracle não são alterados pela formatação de exibição.

**Nota:** esta melhoria é visual e não altera o classificador, as regras dos agentes, as consultas SQL ou os critérios de segurança. A conexão Oracle deve ser configurada no PowerShell **antes** de executar o aplicativo.

## 9. Estruturas de dados e arquitetura computacional

### 9.1 Estruturas

Já existem **listas, dicionários e DataFrames** no código: registros horários são reunidos em uma lista de dicionários e convertidos em tabela pandas; a IA mantém histórico e rastreamento na sessão. Esses usos apoiam armazenamento sequencial, consulta tabular e organização de estado.

**A aprofundar no relatório:** justificar a escolha dessas estruturas (ordem, busca, custo e simplicidade); caso a equipe opte por fila, pilha, tabela hash, árvore ou grafo, implementar e demonstrar uma aplicação coerente, como priorização de alertas ou relacionamento entre módulos. Não afirmar que todas essas estruturas já foram implementadas.

### 9.2 CPU, GPU, memória e eficiência

A execução atual é uma aplicação Python local, de pequeno porte, adequada a **CPU**. Uma GPU, NPU ou TPU não é exigida para a demonstração. Para maior escala, a equipe pode **discutir conceitualmente**:
- CPU para controle, menus, validação e consultas;
- paralelismo e aceleradores para volumes maiores de simulações/modelos;
- RAM para tabelas temporárias e a importância de reduzir cópias desnecessárias;
- armazenamento persistente para histórico e auditoria;
- movimentação de dados como possível gargalo e fonte de consumo de energia;
- eficiência computacional como parte da sustentabilidade da colônia.

Esses pontos são **diretrizes para a explicação de arquitetura**, não medições de desempenho nem implementação de aceleração.

## 10. Sustentabilidade, cidadania digital e responsabilidade

Na apresentação e no relatório, relacionar o funcionamento específico do SIFSM com pelo menos **quatro aspectos** previstos no enunciado. Os seguintes tópicos formam uma proposta de análise a desenvolver:

1. **Uso responsável de recursos:** observar geração, consumo, déficit e excedente para reduzir desperdícios.
2. **Simulação antes da implantação:** testar tempestades fictícias e cenários de bateria sem colocar sistemas reais em risco.
3. **Autonomia e resiliência:** discutir armazenamento, alertas e manutenção de serviços essenciais em cenários de geração reduzida.
4. **Privacidade e transparência:** limitar acesso a dados operacionais e pessoais, registrar recomendações e manter revisão humana.
5. **Impacto computacional:** considerar energia e infraestrutura necessárias ao processamento, armazenamento e IA.
6. **Inovação responsável:** reconhecer que previsões e respostas são limitadas por dados sintéticos, hipóteses e erros de modelos.

**Não** atribuir à aplicação impactos ambientais medidos, garantia de segurança ou desempenho real que ainda não tenham sido demonstrados.

## 11. Testes e validação

Instalar o \`pytest\` se necessário:

\`\`\`powershell
python -m pip install pytest
\`\`\`

Executar:

\`\`\`powershell
python -m pytest tests/ -v
python -m unittest discover -s tests -v
\`\`\`

\`tests/test_modulos.py\` contém testes da simulação, conservação de energia, CSV e regressão; \`tests/test_simulation.py\` contém testes com \`pytest\` para validação de entradas da camada de serviços. A execução local dos testes **não valida** automaticamente a conexão Oracle, a implantação do banco ou o cenário completo integrado.

**Roteiro mínimo de validação manual:**
1. Abrir \`codigo_fonte.py\` e verificar se o menu aparece.
2. Selecionar **2 → 1** e conferir geração de 168 linhas de dados.
3. Selecionar **2 → 2** para consultar registros e **2 → 3** para calcular regressão.
4. Verificar alertas, déficit e limites da bateria nos resultados.
5. Selecionar **3 → 3** e testar status da IA **somente se** o banco estiver configurado.
6. Quando o CRUD for implementado, testar cadastro, consulta, alteração, exclusão e entradas inválidas.
7. Registrar evidências dos testes e das limitações para o relatório e vídeo.

## 12. Entrega da atividade

O enunciado solicita **vídeo de no máximo 5 minutos**, publicado no YouTube como **Não listado**, e uma pasta **.zip** com arquivos padronizados. Checklist:

| Arquivo solicitado | Situação atual |
| --- | --- |
| \`codigo_fonte.py\` ou \`notebook_projeto.ipynb\` | **Presente**: \`codigo_fonte.py\` |
| \`banco_aurora_siger.sql\` ou \`script_banco.sql\` | **Presente**: script de estrutura (execução Oracle não confirmada) |
| \`dados_aurora_siger.csv\` / \`.json\` / \`.txt\` | **Presente**: CSV; atualizar após a última simulação validada |
| \`circuito_logico.pdf\` / \`.png\` ou \`link_tinkercad.txt\` | **Pendente**, caso a equipe escolha essa representação |
| \`simulacao_computacional.py\` / \`.ipynb\` / \`.m\` | **Código presente em \`src/simulation.py\`**; conferir exigência de nome padronizado ao empacotar |
| \`relatorio_tecnico.md\` ou \`.pdf\` | **Arquivo presente, conteúdo ainda pendente** |
| \`README.md\` | **Este documento** |
| \`link_video.txt\` | **Arquivo presente, link ainda pendente** |
| \`graficos_ou_imagens/\` | Opcional, caso sejam produzidas evidências |

O vídeo deve demonstrar ou explicar, de forma compatível com o que estiver implementado: objetivo, dados e banco, CRUD, tratamento de erros, regra lógica e eventual circuito, estruturas de dados, simulação e matemática, regressão, IA, arquitetura computacional, sustentabilidade e execução prática.

**Antes de compactar:** testar a instalação em ambiente limpo, remover segredos, incluir arquivos necessários, preencher o relatório e o link do vídeo, revisar os nomes exigidos e excluir caches (\`__pycache__\`), ambientes virtuais e arquivos temporários do pacote final.

### 12.1 Menus de relatórios e configurações (nova integração)

O menu **4 — Relatórios** permite consultar um resumo energético do CSV local, visualizar alertas e exportar um resumo por dia para `relatorios/resumo_energetico_por_dia.csv`. A consulta ao histórico no Oracle apresenta até dez simulações existentes no schema, quando a conexão estiver configurada. É uma operação **somente de leitura** e não sincroniza automaticamente o CSV com o banco.

O menu **5 — Configurações** permite testar a conexão Oracle (consulta `SELECT 1 FROM dual`), verificar quais variáveis de ambiente foram configuradas sem expor senhas, consultar informações do sistema e conferir a presença de arquivos e bibliotecas. Essa checagem não substitui os testes de execução.

Os dois menus estão conectados a `src/reports.py` e `src/system_status.py`. A opção **1 — Gestão de dados** continua reservada para o CRUD do integrante responsável, sem alterações até a entrega. O conteúdo foi adicionado em branch de integração e requer validação local com o Oracle.

## 13. Próximos passos da equipe

- [ ] Confirmar com o responsável pelo banco se o Oracle já foi implantado.
- [ ] Implementar CRUD funcional e demonstrá-lo pelo menu.
- [ ] Conectar dados da simulação ao esquema Oracle, se definido como arquitetura final.
- [ ] Criar o circuito/diagrama lógico ou a representação escolhida pela equipe.
- [ ] Formalizar e justificar estruturas de dados no relatório.
- [ ] Conectar uma análise final integrada de sustentabilidade ao fluxo do usuário.
- [ ] Consolidar seção de arquitetura computacional e impactos socioambientais no relatório.
- [ ] Criar testes de integração com banco e fluxo completo.
- [ ] Atualizar \`requirements.txt\` para conter todas as dependências de testes, quando padronizado.
- [ ] Completar \`relatorio_tecnico.md\` e gravar o vídeo de até 5 minutos.
- [ ] Preencher \`link_video.txt\`, revisar o ZIP e validar entrega.

## 14. Colaboração e branches

O trabalho é desenvolvido em equipe. Cada integrante pode criar sua branch, abrir Pull Request para \`main\`, revisar o diff e executar testes antes de mesclar. Mudanças de interface, banco, IA ou simulação devem atualizar este README quando alterarem funcionalidades, dependências, instruções ou estado dos requisitos.

**Repositório:** [SIFSM_Aurora_Siger](https://github.com/lucasgesini45-coder/SIFSM_Aurora_Siger)

---

**Nota acadêmica:** este README distingue funcionalidades comprováveis pelo código de propostas ainda pendentes. O documento deve evoluir com o protótipo até a entrega final.
