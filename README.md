# BanVic 360 — Portfolio de Engenharia de Dados

Simulação de um banco nacional brasileiro (2023–2026) resolvida com **9 stacks diferentes**,
sempre chegando nos mesmos **8 KPIs validados por um gabarito imutável**.

> **Tese:** Um problema bancário real, 9 abordagens técnicas, uma única resposta correta.

---

## Os 9 Projetos

| # | Stack | Principal habilidade | Pergunta respondida |
|---|---|---|---|
| 1 | SQL + PostgreSQL | Modelagem dimensional e SQL avançado | Como construir um DW com zero dependências? |
| 2 | Python + PostgreSQL | ETL programático com pandas e psycopg2 | Quando as regras de negócio exigem mais controle? |
| 3 | Apache Hop | ETL visual e operação low-code | Quando uma interface visual faz mais sentido? |
| 4 | Docker | Reprodutibilidade e infraestrutura local | Como eliminar o "funciona só na minha máquina"? |
| 5 | Airflow | Orquestração, dependências e backfill | Como operar pipelines recorrentes com segurança? |
| 6 | dbt | ELT, testes, documentação e lineage | Como organizar transformação SQL em equipe? |
| 7 | Databricks | Processamento distribuído e Lakehouse | Como lidar com volumes maiores e histórico ACID? |
| 8 | n8n | Integrações, APIs e automação low-code | Quando automatizar fluxos orientados a eventos? |
| 9 | Fabric + Power BI | Plataforma integrada e entrega ao negócio | Como entregar dados até o dashboard executivo? |

Cada projeto carrega os mesmos dados, calcula os 8 KPIs e compara automaticamente com o gabarito.

---

## Estrutura de Pastas

```
banvic/
├── data/
│   ├── banvic/          # CSVs originais (998 clientes, 72k transacoes) — IMUTAVEL
│   └── sintetico/       # Dados sinteticos gerados (50k clientes, 3M+ transacoes)
├── external_data/       # 14 datasets publicos (BCB, IBGE, Open-Meteo)
├── sql/
│   ├── 00_setup/        # Schemas e extensoes PostgreSQL
│   ├── 01_bronze/       # DDL e carga bruta (COPY)
│   ├── 02_silver/       # Transformacoes e Data Quality
│   └── 03_gold/         # Star schema dimensional (9 dims + 9 fatos + 8 KPI views)
├── scripts/             # Scripts Python utilitarios
├── projetos/            # Os 9 projetos (cada um em sua pasta)
├── docs/                # Arquitetura, gabarito, roadmap
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Pré-requisitos

- Python 3.10+
- Docker e Docker Compose
- PostgreSQL 15+ (ou use o docker-compose incluído)

---

## Início Rápido (Docker)

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env

# 2. Subir banco de dados
docker compose up -d

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Gerar dados sintéticos (primeira vez)
python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42

# 5. Carregar e validar (setup -> bronze -> silver -> gold -> validação)
python scripts/entrypoint.py
```

Após o passo 5:
- PostgreSQL disponível em `localhost:5432`
- pgAdmin disponível em `http://localhost:5050` (admin@banvic.local / admin)
- 8 KPIs validados contra o gabarito

---

## Os 8 KPIs — Gabarito Imutável

Todo projeto deve reproduzir exatamente estes resultados:

| # | KPI | Lógica |
|---|---|---|
| 1 | Saldo sob gestão por agência | `SUM(saldo_total) GROUP BY agencia` |
| 2 | Volume de transações por mês e tipo | `SUM(valor), COUNT GROUP BY mes, nome_transacao` |
| 3 | Mix de transações (%) | `% de cada tipo sobre total do mês` |
| 4 | Conversão de propostas | `COUNT por status_proposta + valor médio` |
| 5 | Ranking de agências | `Saldo + volume ordenado DESC` |
| 6 | Carteira por colaborador | `Contas geridas, saldo, propostas aprovadas` |
| 7 | Segmentação por faixa etária | `Faixas etárias vs saldo médio` |
| 8 | Correção IPCA | `valor_real = valor_nominal × indice_base / indice_mes` |

Gabarito calculado em: `docs/gabarito/gabarito.json`

---

## Dados

| Fonte | Registros | Descrição |
|---|---|---|
| `data/banvic/` | ~72k transações | Dados originais do banco (imutáveis) |
| `data/sintetico/` | 2.6M+ transações | Expansão sintética (50k clientes) |
| `external_data/` | 14 datasets | BCB (Selic, CDI, IPCA), IBGE, Open-Meteo |

### Escala dos dados sintéticos

| Arquivo | Registros | Distribuição |
|---|---|---|
| `clientes_sinteticos.csv` | 50.000 | Renda lognormal (mediana ~R$3.5k), score correlacionado com renda |
| `contas_sinteticas.csv` | ~70.000 | 1–3 contas por cliente, 65% têm 1 conta |
| `transacoes_sinteticas.csv` | 2.642.400 | Sazonalidade mensal (dez=140%, fev=80%) |
| `propostas_sinteticas.csv` | ~56.000 | Taxa de aprovação varia por faixa de score |
| `investimentos.csv` | ~16.000 | Probabilidade maior com renda e score altos |
| `cartoes.csv` | ~537.000 | Faturas mensais; 75% pagam total |
| `seguros.csv` | ~17.000 | 25% são cross-sell |
| `inadimplencia.csv` | ~468 | Buckets 0-30 / 31-60 / 61-90 / 90+ dias |
| `fraudes.csv` | ~1.400 | 65% tentativas, 35% confirmadas |
| `agencias_expandidas.csv` | 100 | Timeline: 10 (2023) → 20 (2024) → 50 (2025) → 100 (2026) |
| `colaboradores_expandidos.csv` | 1.200 | 4 níveis hierárquicos com cargo, salário e agência |

Todos os dados sintéticos são reprodutíveis com `--seed 42`.

---

## Documentação

- [Arquitetura](docs/arquitetura-lakehouse-banvic.md)
- [Roadmap](docs/roadmap-portfolio-banvic.md)
- [Gabarito dos KPIs](docs/gabarito/gabarito_resumo.txt)
- [Data Quality Framework](sql/02_silver/data_quality_framework.sql)

---

## Quando Usar Cada Stack

A resposta é sempre contextual — depende do time, do volume e da criticidade do pipeline:

| Cenário | Stack recomendada |
|---|---|
| Dados pequenos, equipe SQL-first | PostgreSQL puro |
| Regras de negócio complexas | Python + PostgreSQL |
| Equipe low-code / BI | Apache Hop |
| Reprodutibilidade garantida | Docker |
| Pipelines em produção com retry | Airflow |
| Transformação governada em equipe | dbt |
| Dados > 100GB ou streaming | Databricks |
| Integrações rápidas com APIs | n8n |
| Organização Microsoft-first | Fabric + Power BI |
