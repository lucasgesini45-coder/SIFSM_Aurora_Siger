# Análise da execução entregue

Semente 42; 168 intervalos de uma hora; hipóteses didáticas descritas no README.

## Balanço dos sete dias

| Indicador | Valor |
|---|---:|
| Energia gerada (kWh) | 2640.308 |
| Demanda total (kWh) | 2343.483 |
| Perdas (kWh) | 101.497 |
| Excedente (kWh) | 491.914 |
| Demanda não atendida (kWh) | 262.627 |
| Bateria final (kWh) | 206.040 |
| Horas com alerta | 38 |

## Totais diários

| Dia | Geração (kWh) | Demanda (kWh) | Déficit (kWh) | Bateria final (kWh) |
|---|---:|---:|---:|---:|
| 1 | 470.79 | 337.68 | 0.00 | 207.82 |
| 2 | 470.37 | 333.39 | 0.00 | 208.99 |
| 3 | 476.58 | 333.52 | 0.00 | 205.69 |
| 4 | 143.78 | 335.29 | 0.00 | 3.25 |
| 5 | 143.07 | 331.44 | 185.97 | 0.00 |
| 6 | 464.21 | 331.06 | 76.66 | 190.42 |
| 7 | 471.51 | 341.11 | 0.00 | 206.04 |

## Regressão e interpretação

Equação: consumo = 0.00064711 × hora + 13.855302.

Treino: 134 horas; teste: 34 horas. MAE: 1.8829 kW; RMSE: 1.9730 kW; R²: -0.0096.

MAE da média do treino: 1.8861 kW. A diferença para o modelo linear é mínima; não demonstra uma vantagem preditiva consistente.

Estimativa ilustrativa para a hora 168: 13.9640 kW. Não há observação dessa hora no CSV para validar a estimativa.

O R² negativo mostra que a tendência linear explica mal o consumo cíclico. A tempestade afeta a geração, não o consumo definido no simulador. Para estudar seu impacto, compare os balanços diários e o déficit; essa regressão não prevê geração ou tempestades.

O déficit mostra que a configuração proposta não mantém toda a demanda atendida. A avaliação de alternativas deve simular novas capacidades de bateria, geração ou políticas de consumo; esta execução não determina um dimensionamento ótimo.

## Validação

Seis testes automatizados passaram: reprodução e horários; balanço energético e limites; ida e volta do CSV; reta conhecida; entradas inválidas; alvo constante.