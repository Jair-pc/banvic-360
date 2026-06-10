# Projeto 2 — Python + PostgreSQL

Pipeline ETL completo do BanVic 360 implementado em Python com psycopg2, pandas e SQLAlchemy,
sem depender do cliente `psql` ou de scripts SQL avulsos.

**Pergunta central:** _Quando Python bate SQL — e quando não bate?_

---

## Stack técnica

| Técnica | Arquivo | Por que usei |
|---|---|---|
| `pd.read_sql` + `to_sql` | `etl/silver.py` | I/O eficiente entre pandas e PostgreSQL |
| `np.select` como `CASE WHEN` | `etl/silver.py` | Derivar canal e faixa etária em vetores |
| `df.merge` como SQL JOIN | `etl/gold_fatos.py` | Resolver FKs surrogate sem SQL |
| `UPDATE FROM` via temp table | `etl/gold_dims.py` | Enriquecimento de dim_tempo com macroeconomia |
| Context manager psycopg2 | `etl/conexao.py` | Controle transacional seguro |
| SQLAlchemy `engine.begin()` | `etl/conexao.py` | Commit atômico via with-statement |
| Notebook como exploração | `notebooks/` | Análise interativa e visualizações dos KPIs |

---

## Estrutura dos arquivos

```
02-python-postgresql/
├── etl/
│   ├── conexao.py       Conexao psycopg2 + SQLAlchemy, helper truncar()
│   ├── silver.py        10 transforms Bronze->Silver em pandas
│   ├── gold_dims.py     6 funcoes de carga das dimensoes Gold
│   ├── gold_fatos.py    3 funcoes de carga das tabelas fato
│   └── pipeline.py      Orquestrador com timing por etapa
├── notebooks/
│   └── 01_pipeline_banvic.ipynb  Exploracao + visualizacoes interativas
└── run.py               CLI: python run.py [--etapa silver|gold_dims|gold_fatos]
```

---

## Como executar

### Pré-requisitos
- Docker Compose rodando (`docker compose up -d`)
- Bronze carregado (`python scripts/carga_bronze.py`)
- Gold DDL criado (`sql/03_gold/ddl_modelo_dimensional.sql`)

### Pipeline completo

```bash
python projetos/02-python-postgresql/run.py
```

### Por etapa

```bash
# Apenas Silver
python projetos/02-python-postgresql/run.py --etapa silver

# Dims e fatos Gold
python projetos/02-python-postgresql/run.py --etapa gold_dims gold_fatos
```

### Notebook

```bash
pip install jupyter matplotlib
jupyter notebook projetos/02-python-postgresql/notebooks/01_pipeline_banvic.ipynb
```

### Validar KPIs

```bash
python scripts/validar_gabarito_pg.py
```

---

## Resultado

```
Resultado: 7/7 KPIs corretos
APROVADO: todos os KPIs batem com o gabarito.
```

---

## SQL Puro vs Python

| Critério | Projeto 1 (SQL) | Projeto 2 (Python) |
|---|---|---|
| Testabilidade unitária | Baixa | **Alta** — cada função isolável |
| Debug interativo | Difícil | **Fácil** — `df.head()`, `df.info()` |
| Performance bruta | Melhor | Overhead de memória |
| Integração com ML | Impossível | **Nativa** |
| Reutilização de lógica | Difícil | **Fácil** — funções Python |
| Dependências | Nenhuma | psycopg2, pandas, SQLAlchemy |

## Quando usar Python + PostgreSQL

| Cenário | Python + PG é ideal? |
|---|---|
| Time Python-first (data scientists, ML engineers) | **Sim** — sem curva de SQL avançado |
| Transformações com lógica de negócio complexa | **Sim** — código testável e modular |
| Integração com APIs externas ou ML models | **Sim** — nativo |
| Exploração interativa de dados | **Sim** — notebooks |
| Pipeline de alta performance (100M+ linhas) | **Não** — use Spark ou Databricks |
| Time 100% SQL com DW maduro | **Não** — SQL Puro ou dbt |

Python com pandas é a abordagem certa para times que preferem código sobre SQL,
especialmente quando as regras de negócio crescem além do que uma query consegue expressar
com clareza. O custo é performance e a necessidade de gerenciar dependências.
