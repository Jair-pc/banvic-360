# BanVic 360 — Portfolio de Engenharia de Dados

> **"O mesmo problema. 9 ferramentas diferentes. Uma única resposta correta."**

---

## A História por Trás Deste Projeto

### O problema com a maioria dos portfólios de dados

A maioria dos projetos de portfólio de Engenharia de Dados segue o mesmo roteiro:

- Pegar um dataset do Kaggle (Titanic, vendas de e-commerce, dados de filmes)
- Limpar com pandas, salvar num banco
- Fazer um gráfico bonito
- Chamar de "pipeline ETL"

Isso não representa o trabalho real. Não representa os desafios reais. E não mostra se a pessoa consegue trabalhar em um ambiente profissional de verdade.

Eu decidi fazer diferente.

---

### Por que simulei um banco real

Em projetos anteriores, trabalhei com datasets simplificados — poucos campos, sem relacionamentos complexos, sem sazonalidade, sem dados macroeconômicos, sem hierarquias.

Para este portfólio, me perguntei: **qual seria um problema de dados suficientemente complexo para cobrir tudo que um engenheiro de dados enfrenta na vida real?**

A resposta: **um banco nacional brasileiro em crescimento.**

O **BanVic (Banco Vitória)** tem:
- Clientes com perfis financeiros realistas (renda, score de crédito, faixa etária)
- Contas, transações, propostas de crédito, investimentos, seguros, inadimplência, fraudes
- 100 agências com expansão histórica (2023 → 2026)
- 1.200 funcionários em 4 níveis hierárquicos
- Dados macroeconômicos reais do Banco Central e do IBGE (Selic, IPCA, PIB, população)
- Sazonalidade nas transações (dezembro tem 40% a mais)
- 3 milhões de transações e 50.000 clientes

Não é um dataset simplificado. É uma simulação realista do que você encontra em uma empresa de médio porte.

---

### Por que 9 ferramentas para o mesmo problema

No mercado de dados de hoje, **não existe uma ferramenta certa**. Existe a ferramenta certa **para aquele contexto**.

E o contexto muda dependendo de quem pergunta:

> *"Quero ver os dados hoje."* — O gestor de negócio
>
> *"Precisa rodar todo dia sem falhar."* — O diretor de operações
>
> *"O time não sabe programar."* — O líder de projetos
>
> *"Temos 500 GB novos por dia."* — O CTO
>
> *"Quanto vai custar?"* — O CFO

A resposta para cada um é diferente. E um engenheiro de dados que só sabe uma ferramenta vai sempre dar a mesma resposta — independente da pergunta.

**Este projeto demonstra que eu consigo escolher a ferramenta certa dependendo do que o projeto exige — e justificar essa escolha com números.**

---

### O que todos os 9 projetos têm em comum

- Os mesmos dados (o BanVic)
- O mesmo modelo dimensional (Bronze → Silver → Gold)
- As mesmas 8 perguntas para responder (KPIs)
- O mesmo gabarito para validar

A única coisa que muda é **como** chegamos lá.

---

## Comparativo: Qual Caminho Seguir?

A tabela abaixo é o coração deste projeto. Ela responde a pergunta que todo gestor faz antes de aprovar um pipeline:

| # | Ferramenta | Custo mensal estimado | Velocidade de entrega | Escala | Quem mantém | Melhor quando... |
|---|---|---|---|---|---|---|
| 1 | SQL + PostgreSQL | Gratuito | Rápida | Até ~50 GB | DBA / Eng. Dados | Time SQL-first, pipeline simples |
| 2 | Python + PostgreSQL | Gratuito | Média | Até ~50 GB | Dev Python | Regras de negócio complexas |
| 3 | Apache Hop | Gratuito | Média | Até ~50 GB | Qualquer um | Time sem programadores |
| 4 | Docker | Gratuito | — | Qualquer | Dev / DevOps | Padronização de ambiente |
| 5 | Airflow | R$ 200–800/mês (gerenciado) | Média | Até ~200 GB | Eng. Dados | Pipeline em produção com retry |
| 6 | dbt | Gratuito (Core) | Rápida | Qualquer DW | Eng. / Analista | SQL organizado em equipe |
| 7 | Databricks | R$ 500–5.000/mês | Rápida (cluster) | Petabytes | Eng. Sênior | Volumes grandes, ML |
| 8 | n8n | Gratuito (self-hosted) | Muito rápida | Até ~50 GB | Qualquer um | Automações, APIs, times mistos |
| 9 | Fabric + Power BI | R$ 50/usuário/mês | Rápida | Até ~100 TB | Analista / Eng. | Org. Microsoft, entrega ao negócio |

### Velocidade de entrega (tempo até o primeiro resultado)

```
SQL Puro        ████████████████████  Rápido — um arquivo .sql e você vê o resultado
Python + PG     ████████████████      Médio — precisa escrever as funções
Apache Hop      ████████████████      Médio — arrastar blocos leva tempo inicial
Airflow         ████████████          Mais lento — setup de infraestrutura
dbt             ████████████████████  Rápido — models SQL com convenção clara
Databricks      ████████████████      Médio — setup do cluster e uploads
n8n             ████████████████████  Muito rápido — blocos prontos, só configurar
```

### Quando o custo começa a importar

- **Projetos pessoais e pequenas empresas:** SQL Puro, Python, Apache Hop, dbt Core e n8n self-hosted custam zero.
- **Médias empresas com pipeline em produção:** Airflow gerenciado (Astronomer, MWAA) fica entre R$ 500–2.000/mês.
- **Escala grande (>100 GB/dia):** Databricks ou Fabric são necessários — mas o custo se justifica quando a alternativa é processar isso em uma única máquina e falhar.

A pergunta certa não é *"qual é o mais barato?"*, mas *"qual é o mais barato que ainda resolve o problema?"*

---

## Os 9 Projetos

| # | Ferramenta | Principal habilidade demonstrada | Pergunta respondida |
|---|---|---|---|
| 1 | SQL + PostgreSQL | Modelagem dimensional, SQL avançado, star schema | Como construir um DW com zero dependências? |
| 2 | Python + PostgreSQL | ETL programático, pandas, psycopg2 | Quando Python supera SQL puro? |
| 3 | Apache Hop | ETL visual, low-code, lineage automático | Quando uma interface visual faz mais sentido? |
| 4 | Docker | Reprodutibilidade, containerização, CI/CD | Como eliminar o "funciona só na minha máquina"? |
| 5 | Airflow | Orquestração, scheduling, retry, paralelismo | Como operar pipelines recorrentes com segurança? |
| 6 | dbt | ELT, testes automáticos, documentação, lineage | Como organizar transformação SQL em equipe? |
| 7 | Databricks | PySpark, Delta Lake, processamento distribuído | Como lidar com volumes que não cabem numa máquina? |
| 8 | n8n | Automação visual, webhooks, integrações de API | Quando automatizar sem escrever código? |
| 9 | Fabric + Power BI | Plataforma integrada Microsoft, entrega ao negócio | Como entregar dados direto no dashboard do gestor? |

Cada projeto usa os mesmos dados, calcula as mesmas 8 KPIs e compara automaticamente com o gabarito. **A resposta é sempre a mesma. O caminho é sempre diferente.**

---

## As 8 KPIs — O Gabarito Imutável

Todo projeto precisa responder exatamente essas 8 perguntas e chegar nos mesmos números:

| # | Pergunta de negócio | Como calcular |
|---|---|---|
| 1 | Quanto dinheiro cada agência tem sob gestão? | Soma dos saldos agrupada por agência |
| 2 | Qual foi o volume de transações por mês e tipo? | Soma e contagem agrupadas por mês e tipo |
| 3 | Qual o mix percentual de cada tipo de transação? | % de cada tipo sobre o total do mês |
| 4 | Quantas propostas de crédito foram aprovadas? | Contagem por status + valor médio de aprovação |
| 5 | Qual o ranking das agências? | Agências ordenadas por saldo + volume |
| 6 | Qual a carteira de cada colaborador? | Contas geridas, saldo total, propostas aprovadas |
| 7 | Como os clientes se distribuem por faixa etária? | Faixas de 18–24, 25–34, 35–44, 45–54, 55–64, 65+ vs saldo médio |
| 8 | Qual o valor real das transações corrigido pelo IPCA? | Valor nominal × índice base ÷ índice do mês |

O gabarito foi calculado a partir dos dados originais do banco. É a fonte da verdade — qualquer projeto que chegar em um número diferente tem um erro.

---

## A Arquitetura — Bronze, Silver, Gold

Independente da ferramenta, todos os projetos seguem a mesma arquitetura de camadas:

```
FONTES
  ├── data/banvic/          Dados originais do banco (imutáveis)
  ├── data/sintetico/       Expansão sintética para volume real
  └── external_data/        BCB (Selic, CDI, IPCA), IBGE, clima

        ↓ ingestão bruta

BRONZE — dados como chegaram, sem transformação
  Objetivo: guardar tudo, nunca perder nada

        ↓ limpeza + tipagem

SILVER — dados limpos, padronizados, com qualidade verificada
  Objetivo: confiável para análise

        ↓ modelagem dimensional

GOLD — star schema (dimensões + fatos + KPI views)
  Objetivo: rápido para consultar, fácil de entender
```

Esta arquitetura tem um nome no mercado: **Lakehouse**. É usada por Databricks, Microsoft Fabric, Snowflake e a maioria das plataformas modernas. Implementar ela em 9 stacks diferentes mostra que o conceito é independente da ferramenta.

---

## Estrutura do Repositório

```
banvic-360/
├── data/                    ← Dados do banco (baixar do Drive — veja abaixo)
│   ├── banvic/              Dados originais: 998 clientes, 72k transações
│   └── sintetico/           Dados gerados: 50k clientes, 3M+ transações
├── external_data/           ← Dados públicos: BCB, IBGE, Open-Meteo (baixar do Drive)
├── sql/
│   ├── 00_setup/            Configuração inicial do banco (schemas + extensões)
│   ├── 01_bronze/           DDL e carga dos CSVs
│   ├── 02_silver/           Transformações e Data Quality Framework
│   └── 03_gold/             Modelo dimensional (9 dims + 9 fatos + 8 KPI views)
├── scripts/                 Scripts Python utilitários (ver scripts/README.md)
├── projetos/                Os 9 projetos (01 ao 09), cada um independente
├── docker-compose.yml       Sobe PostgreSQL 15 + pgAdmin
├── requirements.txt         Dependências Python
└── .env.example             Variáveis de configuração (copiar para .env)
```

---

## Como Começar

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/banvic-360.git
cd banvic-360
```

### 2. Baixar os dados

Os arquivos CSV não ficam no GitHub (são grandes). Baixe do Drive:

```
https://drive.google.com/drive/folders/1mtIBYJss1RqkfT_trxrcH5nanoiBHiuq?usp=sharing
```

Após baixar:
- Pasta `banvic/` e `sintetico/` → colocar dentro de `data/`
- Pastas `macroeconomia/`, `geografia/`, `clima/`, `projecoes/` → colocar dentro de `external_data/`

Ou gere os dados sintéticos do zero (requer Python e ~15 min):

```bash
pip install -r requirements.txt
python scripts/download_datasets.py           # baixa dados do BCB/IBGE
python scripts/expandir_agencias.py           # gera 100 agências
python scripts/expandir_colaboradores.py      # gera 1.200 colaboradores
python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42
python scripts/projetar_series_historicas.py
```

### 3. Configurar o ambiente

```bash
cp .env.example .env
```

### 4. Subir o banco de dados

```bash
docker compose up -d
# PostgreSQL em localhost:5432
# pgAdmin em http://localhost:5050  (admin@banvic.local / admin)
```

### 5. Carregar os dados e validar

```bash
python scripts/entrypoint.py
```

Este comando faz tudo: cria os schemas, carrega os CSVs no Bronze, transforma em Silver, monta o Gold e verifica as 8 KPIs contra o gabarito.

---

## Pré-requisitos

- Python 3.10+
- Docker Desktop
- 4 GB de RAM disponível
- ~2 GB de espaço em disco (para os dados)

---

## Escala dos Dados Sintéticos

Todos gerados com `--seed 42` — rodar duas vezes produz os mesmos números.

| Arquivo | Registros | Como foi gerado |
|---|---|---|
| Clientes | 50.000 | Renda com distribuição lognormal, score correlacionado com renda |
| Contas | ~70.000 | 1 a 3 contas por cliente, 65% têm só 1 |
| Transações | 2.642.400 | Sazonalidade mensal preservada (dezembro = +40%) |
| Propostas de crédito | ~56.000 | Taxa de aprovação varia pelo score do cliente |
| Investimentos | ~16.000 | Patrimônio ativo de R$ 273 milhões |
| Cartões (faturas) | ~537.000 | Faturas mensais, 75% pagam total |
| Seguros | ~17.000 | 25% são cross-sell |
| Inadimplência | ~468 | Buckets 0–30 / 31–60 / 61–90 / 90+ dias |
| Fraudes | ~1.400 | 35% confirmadas, 65% tentativas |
| Agências | 100 | Crescimento: 10 (2023) → 20 (2024) → 50 (2025) → 100 (2026) |
| Colaboradores | 1.200 | 4 níveis hierárquicos, salários por faixa de cargo |
