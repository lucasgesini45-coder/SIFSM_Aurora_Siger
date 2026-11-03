# Aurora Siger — Fase 7 • Pessoa 3

Entrega: simulação e análise de dados. Os parâmetros abaixo são hipóteses didáticas autorizadas pelo aluno, não números extraídos do enunciado nem um modelo físico validado de Marte. Confirme-os com o grupo antes de integrar a entrega.

## Executar no VS Code

1. Extraia o ZIP e abra a pasta `aurora_pessoa3` no VS Code.
2. Use Python 3.11 ou 3.12. No terminal, crie o ambiente: `python -m venv .venv`.
3. No Windows PowerShell, ative com `.venv\Scripts\Activate.ps1`; em macOS/Linux: `source .venv/bin/activate`. Se o PowerShell bloquear a ativação, use diretamente `.venv\Scripts\python.exe` no lugar de `python` nos comandos seguintes.
4. Instale: `python -m pip install -r requirements.txt`.
5. Gere os dados: `python -m src.simulation`.
6. Analise o CSV: `python -m src.regression`.
7. Execute os testes: `python -m unittest discover -s tests -v`.

Os comandos devem ser executados na pasta que contém este README. A execução do módulo de simulação substitui o CSV da pasta do projeto. O relatório ANALISE.md registra a execução entregue; se alterar as hipóteses, atualize também o relatório.

## Contrato de integração

```python
from src.simulation import gerar_simulacao, exportar_csv
from src.regression import calcular_regressao

dados = gerar_simulacao(horas=168)
resultado = calcular_regressao(dados)
exportar_csv(dados, 'dados_aurora_siger.csv')
```

`gerar_simulacao(horas=168)` retorna um DataFrame e não grava arquivos automaticamente. Aceita inteiro positivo; reinicia um gerador NumPy local com semente 42 em cada chamada. `calcular_regressao(dados)` retorna um dicionário com coeficiente angular, intercepto, contagens de treino/teste, MAE, RMSE, R², MAE da referência e estimativa da próxima hora. Exige no mínimo dez registros numéricos finitos, horas únicas não negativas e consumo não negativo. Ordena uma cópia por hora. R² é `None` quando o alvo do teste é constante.

O banco e a IA são de outros responsáveis. O grupo deve combinar esse formato de retorno; não há dependência dessas funções para testar esta entrega.

## Hipóteses e regras

- Sete dias convencionais de 24 horas, não sóis marcianos. Horas 0 a 167, cada registro cobre [hora, hora + 1). Dia inicial 1; hora do dia 0 a 23.
- Consumo agregado: 12 kW de base + 4 kW das 08h às 19h, acrescido de ruído uniforme entre -1 e +1 kW.
- Geração solar: zero fora das 06h–18h. Dentro da janela, 65 × sen(pi × (hora_dia + 0,5 − 6) / 12) × fator aleatório uniforme [0,9; 1,0). É uma aproximação da potência média horária usando o ponto central.
- Nos dias 4 e 5, uma tempestade fictícia reduz a geração a 30% do valor calculado. Em simulações mais longas o evento não se repete.
- Bateria: capacidade de 300 kWh, carga inicial de 240 kWh; eficiência de carga e descarga de 95% em cada sentido; sem limite adicional de potência, autodescarga ou envelhecimento.
- Energia no intervalo = potência média × 1 hora. Saldo = geração − consumo. A soma horária é uma aproximação discreta da integral da potência.
- Com saldo positivo, a bateria recebe energia até a capacidade; sobra é excedente descartado. Com saldo negativo, descarrega até zero; o restante é demanda não atendida, registrada como déficit.
- Alerta quando o estado de carga ao final fica abaixo de 20% ou há déficit maior que 1e-9 kWh. O alerta não aciona corte automático de cargas.

## Dicionário do CSV

CSV UTF-8 com cabeçalho, vírgula como separador, ponto decimal e sem índice extra. Use importação de texto no Excel se a configuração regional não reconhecer as colunas.

| Coluna | Significado/unidade |
|---|---|
| hora | Índice sequencial do intervalo, começando em 0 |
| dia | Dia convencional, começando em 1 |
| hora_dia | Hora local fictícia, 0–23 |
| tempestade | Booleano indicando o cenário adverso |
| geracao_kw / consumo_kw | Potências médias do intervalo |
| saldo_kwh | Geração menos consumo em uma hora |
| bateria_inicio_kwh / bateria_fim_kwh | Energia armazenada antes/depois do intervalo |
| soc_pct | 100 × bateria_fim_kwh / 300 |
| carga_kwh | Energia encaminhada à bateria, antes das perdas |
| descarga_kwh | Energia entregue pela bateria à carga, após perdas |
| perdas_kwh | Perdas de conversão na carga ou descarga |
| excedente_kwh | Energia gerada que não pode ser aproveitada |
| deficit_kwh | Demanda de energia não atendida |
| alerta | Booleano de bateria baixa ou déficit |

Balanço verificado em cada linha:

`geração + bateria_inicial + déficit = consumo + bateria_final + perdas + excedente`

Geração e consumo nessa igualdade são energias do intervalo; numericamente coincidem com as potências por ser um intervalo de 1 h. Nenhum cálculo interno é arredondado; o CSV usa dez casas decimais.

## Entender a regressão

Modelo: `consumo_kw = a × hora + b`. Os primeiros 134 registros treinam o modelo e os últimos 34 avaliam sua previsão, preservando a ordem temporal. O cálculo usa mínimos quadrados: `a = soma((x−média_x)(y−média_y))/soma((x−média_x)²)` e `b = média_y − a × média_x`.

MAE mede erro absoluto médio em kW; RMSE dá mais peso aos erros grandes. R² pode ser negativo: nesse caso a regressão não supera, pela soma dos erros quadráticos, a média do próprio conjunto de teste. A referência operacional comparável usa somente a média do treino. O modelo não é reajustado após a avaliação; a estimativa da próxima hora usa os mesmos coeficientes.

A hora sequencial não explica o ciclo diurno. A análise demonstra essa limitação em vez de apresentar uma previsão artificialmente boa. O consumo da hora 168 é uma extrapolação ilustrativa, sem intervalo de confiança. Melhorias futuras: mais dias, variáveis de horário/atividade, modelo periódico e validação temporal adicional.

## O que estudar em cada arquivo

1. Em simulation.py: validação do argumento, gerador aleatório local, laço horário, condicionais de carga/descarga, construção do DataFrame e exportação.
2. Em regression.py: validação das colunas, separação temporal, fórmulas de mínimos quadrados e métricas.
3. Nos testes: conservação física e continuidade da bateria, reprodutibilidade, leitura do CSV, regressão de uma reta conhecida e rejeição de entradas inválidas.

Os dados são inteiramente sintéticos. Não há dados pessoais ou medições reais. Preservar perdas e déficit evita interpretar bateria limitada como fornecimento ilimitado; essa informação pode apoiar a discussão de sustentabilidade e priorização de cargas pelo restante da equipe.
