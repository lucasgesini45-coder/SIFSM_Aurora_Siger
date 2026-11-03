# SIFSM Aurora Siger

Projeto acadêmico com simulação didática de energia, regressão linear e módulo de IA com Oracle.

## Requisitos

Python 3.11 ou 3.12 e acesso a um banco Oracle para as funções da IA.

```bash
python -m pip install -r requirements.txt
python codigo_fonte.py
```

No menu principal, a opção **2** executa uma simulação sintética de 168 horas, gera `dados_aurora_siger.csv`, consulta o CSV e calcula uma regressão. Esse fluxo **não utiliza nem grava o banco Oracle**. Executar uma nova simulação substitui o CSV.

A opção **3** abre o menu dos agentes de IA (`ia/ia_agentes.py`). Esse módulo consulta as tabelas do Oracle e registra recomendações. Antes de usá-lo, configure as variáveis `ORACLE_USER`, `ORACLE_PASSWORD` e `ORACLE_DSN`, e prepare o esquema com `banco_aurora_siger.sql` em um banco de desenvolvimento. **Atenção:** esse script remove e recria tabelas; não execute sobre dados que queira preservar.

O gerador CSV e os dados Oracle são implementações didáticas distintas. Os campos e premissas de regressão também diferem; integrar persistência e dados exige um mapeamento explícito entre os módulos.

As opções 1, 4 e 5 do menu principal continuam como funcionalidades em desenvolvimento.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes de simulação/regressão são independentes do Oracle. Consulte `docs/README_Pessoa3.md` para hipóteses, parâmetros e limitações da simulação.
