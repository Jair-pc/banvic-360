# Projeto 1 — SQL Puro (PostgreSQL)

## Objetivo

Implementar o pipeline ETL completo do BanVic 360 usando exclusivamente SQL nativo do PostgreSQL,
sem ORM, sem frameworks de orquestração e sem linguagens de programação adicionais.

**Pergunta central:** _Quando SQL puro é suficiente — e quando não é?_

---

## Diferenciais técnicos demonstrados

| Técnica | Arquivo | Propósito |
|---|---|---|
| `EXPLAIN (ANALYZE, BUFFERS)` | `04_kpis_analyze.sql` | Revelar planos de execução e custos reais |
| Índices cobertos (`INCLUDE`) | `03_indices.sql` | Index-only scans evitam acesso ao heap |
| Índices parciais | `03_indices.sql` | `WHERE eh_conta_ativa = TRUE` reduz tamanho do índice |
| Window functions | `02_populate_fatos.sql`, DDL | `ROW_NUMBER OVER(PARTITION BY...)` para deduplicação SCD |
| CTEs para evitar produto cartesiano | DDL (KPI 6) | Separar agregações antes do JOIN final |
| `ON CONFLICT DO NOTHING` | DDL (`dim_tempo`) | Insert idempotente da dimensão calendário |
| `TRUNCATE ... CASCADE` | `01_populate_dims.sql` | Recarga segura respeitando FKs |
| Star schema dimensional | DDL Gold | Modelo padrão de DW para analytics |

---

## Estrutura dos arquivos

```
sql/
├── 01_populate_dims.sql   Silver -> Gold: popula 6 dimensões
├── 02_populate_fatos.sql  Silver -> Gold: popula 3 tabelas fato
├── 03_indices.sql         Índices estratégicos (17 índices, incluindo cobertos e parciais)
└── 04_kpis_analyze.sql    8 KPIs com EXPLAIN ANALYZE para análise de performance
```

---

## Como executar

### Pré-requisitos
- Docker Compose rodando (`docker compose up -d`)
- Bronze carregado (`python scripts/carga_bronze.py`)
- Silver transformado (`sql/02_silver/ddl_silver_transforms.sql`)
- Gold DDL criado (`sql/03_gold/ddl_modelo_dimensional.sql`)

### Ordem de execução

```bash
# 1. Popula dimensões
psql -U banvic_user -d banvic -f projetos/1_sql_puro/sql/01_populate_dims.sql

# 2. Popula fatos (depende das dimensões)
psql -U banvic_user -d banvic -f projetos/1_sql_puro/sql/02_populate_fatos.sql

# 3. Cria índices estratégicos
psql -U banvic_user -d banvic -f projetos/1_sql_puro/sql/03_indices.sql

# 4. Valida KPIs
python scripts/validar_gabarito_pg.py
```

---

## Resultados de performance (EXPLAIN ANALYZE)

| KPI | Operação dominante | Tempo real | Estratégia de índice |
|---|---|---|---|
| KPI 1 | Hash Join 998 linhas | **1,7 ms** | `idx_fc_agencia` (INCLUDE saldo) |
| KPI 2/3 | Hash Join 71.921 linhas | **179 ms** | `idx_ft_tempo_tx_val` (coberto) |
| KPI 4 | Sequential Scan 1.996 propostas | **< 1 ms** | Tabela pequena, seq scan otimizado |
| KPI 5 | CTE + Window Function | **2 ms** | Reusa `vw_kpi1` como CTE |
| KPI 6 | Dupla CTE + Hash Join | **3 ms** | `idx_fc_colaborador`, `idx_fp_colaborador` |
| KPI 7 | Merge Join dim_cliente | **45 ms** | `idx_dc_faixa` (parcial) |
| KPI 8 | Cross Join IPCA + Window | **195 ms** | `idx_dt_ipca` (parcial NOT NULL) |

### Observação sobre índices

Com apenas 998 contas e 71.921 transações, o planejador escolhe Seq Scan para tabelas pequenas
(correto — overhead do índice seria maior). Os índices se tornam relevantes em escala sintética
(50k+ clientes, 2M+ transações).

---

## Validação do gabarito

```
Resultado: 7/7 KPIs corretos
APROVADO: todos os KPIs batem com o gabarito.
```

| KPI | PG (Gold) | Gabarito | Status |
|---|---|---|---|
| 1 — Saldo por agência | R$ 26.509.620,12 | R$ 26.509.620,12 | ✓ |
| 2/3 — Volume transações | R$ 58.122.708,67 | R$ 58.122.708,67 | ✓ |
| 4 — Conversão propostas | 525 Enviada / 513 Aprovada | idem | ✓ |
| 5 — Ranking agências | Agência Digital #1 | idem | ✓ |
| 6 — Carteira colaborador | R$ 26.509.620,12 total | idem | ✓ |
| 7 — Segmentação etária | 50.997 clientes | idem | ✓ |
| 8 — Correção IPCA | R$ 58.122.708,67 nominal | idem | ✓ |

---

## Quando usar SQL Puro

| Cenário | SQL Puro é ideal? |
|---|---|
| Time pequeno com forte background SQL | **Sim** — zero dependências |
| Transformações pontuais ou dashboards finais | **Sim** — lógica vive no banco |
| Pipeline simples (Bronze → Gold em 1-2 passos) | **Sim** — menos camadas = menos bugs |
| Orquestração com retry, alertas, scheduling | **Não** — use Airflow / dbt |
| Linhagem de dados e catálogo automáticos | **Não** — use dbt |
| Escala além de 100 GB ou multi-fonte | **Não** — use Spark / Databricks |
| Versionamento de transformações | **Limitado** — dbt faz melhor |
| Testes unitários de transformações | **Limitado** — dbt + Great Expectations fazem melhor |

### Conclusão

SQL Puro no PostgreSQL é a escolha certa quando a equipe domina SQL e a complexidade
do pipeline cabe em um único banco. É a fundação que todo engenheiro de dados precisa
dominar antes de adicionar camadas de abstração.

O maior risco do SQL puro: **lógica distribuída em múltiplos scripts sem orquestração**.
O Projeto 2 (Python + PostgreSQL) resolve isso; o Projeto 6 (dbt) resolve com elegância máxima.
