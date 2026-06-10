# Projeto 7 — Databricks Lakehouse

Pipeline ELT do BanVic 360 implementado com **PySpark + Delta Lake** no Databricks.
A mesma arquitetura Bronze/Silver/Gold, agora rodando em cluster distribuido com
ACID transactions, time travel e compactacao automatica de arquivos.

**Pergunta central:** _O que muda quando o dado nao cabe mais em uma maquina?_

---

## Stack tecnica

| Conceito Databricks | Uso no projeto | Por que importa |
|---|---|---|
| **Delta Lake** | Bronze + Silver + Gold | ACID, time travel, schema enforcement sem custo extra |
| **PySpark DataFrame API** | Todas as transformacoes | Mesmo codigo escala de 1 para 100 nos |
| **`broadcast()`** | Joins com dimensoes | Evita shuffle de tabelas pequenas — 10x mais rapido |
| **`Window.partitionBy`** | Dedup de clientes | Mesmo padrao do SQL, executado em paralelo |
| **`OPTIMIZE`** | Tabelas grandes | Consolida small files — critico apos muitos appends |
| **Databricks Jobs** | `job_config.json` | Orquestracao nativa com DAG, retries e alertas |
| **Delta Live Tables** | `dlt/` | Abordagem declarativa — voce define O QUE, Databricks cuida do COMO |
| **Time Travel** | Auditoria | Consultar qualquer versao historica de uma tabela |

---

## Estrutura dos arquivos

```
07-databricks/
├── notebooks/
│   ├── 00_setup.py          Cria databases, valida CSVs no DBFS
│   ├── 01_bronze.py         CSV -> Delta Bronze (35 tabelas + OPTIMIZE)
│   ├── 02_silver.py         Bronze -> Silver (DQ + tipagem + UNION + dedup)
│   ├── 03_gold_dims.py      Silver -> Gold (5 dimensoes + dim_tempo 2010-2026)
│   ├── 04_gold_fatos.py     Silver + Bronze -> Gold (3 fatos)
│   └── 05_validar_kpis.py   8 KPIs via Spark SQL + validacao vs gabarito
├── dlt/
│   └── banvic_pipeline_dlt.py  Alternativa declarativa (Delta Live Tables)
├── job_config.json          Databricks Jobs API — DAG completo com agendamento
├── run.bat                  Windows: importa notebooks + cria job via CLI
├── run.sh                   Linux/Mac: idem
└── README.md
```

---

## Como executar

### Pre-requisito: subir os CSVs para o DBFS

Os dados ficam **fora do git** (apenas no Drive e no DBFS).

**Opcao 1 — Databricks CLI:**
```bash
pip install databricks-cli
databricks configure --token
# (informe host: https://community.cloud.databricks.com e token gerado na UI)

databricks fs mkdirs dbfs:/FileStore/banvic/csv
databricks fs cp -r data/banvic/      dbfs:/FileStore/banvic/csv/banvic/
databricks fs cp -r data/sintetico/   dbfs:/FileStore/banvic/csv/sintetico/
databricks fs cp -r external_data/    dbfs:/FileStore/banvic/csv/external_data/
```

**Opcao 2 — UI (mais facil no Community Edition):**
1. Menu lateral: **Catalogo** -> **Adicionar dados** -> **Upload de arquivos**
2. Destino: `/FileStore/banvic/csv/banvic/` para cada subpasta

### Executar no Databricks Community Edition (passo a passo)

1. **Criar cluster:** Calcular -> Criar cluster -> Single Node -> DBR 14.3 LTS
2. **Importar notebooks:** Espaco de trabalho -> Importar -> cada arquivo `.py`
3. **Executar em ordem:** `00_setup` -> `01_bronze` -> `02_silver` -> `03_gold_dims` -> `04_gold_fatos` -> `05_validar_kpis`

### Executar via Databricks CLI (plano pago)

```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh && ./run.sh
```

### Executar localmente (sem Databricks)

Para testar a logica PySpark antes de subir ao cluster:
```bash
pip install pyspark==3.5.1 delta-spark==3.2.0

# Adaptar: remover dbutils, substituir display() por show(), ajustar caminhos
python notebooks/02_silver.py
```

---

## Delta Lake: recursos demonstrados

### Time Travel

```python
# Versao anterior de uma tabela
spark.read.format("delta").option("versionAsOf", 0).table("banvic_bronze.transacoes")

# Ver historico completo
spark.sql("DESCRIBE HISTORY banvic_bronze.transacoes").show()
```

### OPTIMIZE + ZORDER

```python
# Compactar small files (critico apos muitos appends incrementais)
spark.sql("OPTIMIZE banvic_bronze.transacoes")

# ZORDER: co-locar dados frequentemente filtrados juntos
spark.sql("OPTIMIZE banvic_gold.fato_transacoes ZORDER BY (sk_agencia, sk_tempo)")
```

### Schema Evolution

```python
# Adicionar coluna sem recriar a tabela
df_novo.write.format("delta").option("mergeSchema", "true").mode("append").saveAsTable(...)
```

---

## Delta Live Tables (alternativa declarativa)

O arquivo `dlt/banvic_pipeline_dlt.py` mostra a abordagem DLT:

```python
@dlt.table(name="silver_clientes")
@dlt.expect_or_fail("cod_cliente nao nulo", "cod_cliente IS NOT NULL")
@dlt.expect("cpf formato valido", "LENGTH(cpf) = 14")
def silver_clientes():
    # Apenas declare o que a tabela deve conter
    # DLT resolve dependencias, retries e monitoramento
    return ...
```

**DLT vs notebooks manuais:**
| | Notebooks | Delta Live Tables |
|---|---|---|
| Ordem de execucao | Manual | Automatica |
| Retries | Configurar no Job | Embutido |
| Monitoramento de DQ | Manual | Dashboard automatico |
| Lineage visual | Nenhum | Grafico interativo |
| Disponivel no Community | Sim | Nao (requer Premium+) |

---

## Lineage do projeto

```
DBFS /FileStore/banvic/csv/
  banvic/        sintetico/       external_data/
     │                │                 │
     └────────────────┴─────────────────┘
                      │
              01_bronze.py
          banvic_bronze.* (35 Delta tables)
                      │
              02_silver.py
          banvic_silver.clientes    (real + sint + dedup)
          banvic_silver.contas      (real + sint + eh_ativa)
          banvic_silver.transacoes  (real + sint + canal)
          banvic_silver.agencias    (+ lat/lon)
          banvic_silver.colaboradores (expandidos)
          banvic_silver.propostas   (real + sint)
                      │
         03_gold_dims.py            04_gold_fatos.py
         dim_tempo (2010-2026)       fato_contas
         dim_cliente (SCD2)          fato_transacoes
         dim_agencia                 fato_propostas_credito
         dim_colaborador               (bronze direto)
         dim_canal
                      │
              05_validar_kpis.py
              8 KPIs via Spark SQL
```

---

## Comparativo com outros projetos

| Capacidade | SQL Puro | Python/psycopg2 | Airflow | dbt | Databricks |
|---|---|---|---|---|---|
| Escala de dados | Limitada ao PG | Limitada ao PG | Limitada ao PG | Limitada ao DW | **Petabytes** |
| Formato de storage | Tabelas PG | Tabelas PG | Tabelas PG | Tabelas DW | **Delta Lake** |
| Time Travel | Nao | Nao | Nao | Nao | **Sim** |
| Processamento paralelo | Nao | Pandas (1 no) | 1 worker | SQL do DW | **Cluster Spark** |
| ACID em CSV/Parquet | Nao | Nao | Nao | Nao | **Sim (Delta)** |
| Custo | Gratis (local) | Gratis (local) | Gratis (local) | Gratis (local) | **Cloud (pago)** |

O grande diferencial do Databricks nao e a linguagem (PySpark e Python),
nem o modelo de dados (ainda e star schema) — e a **camada de storage**
(Delta Lake) e a **capacidade de processar em cluster**.

Para um banco com 100M de transacoes por dia, os projetos 1-6 simplesmente
nao funcionam. O Databricks e o mesmo pipeline, com os mesmos resultados,
mas que roda independente do tamanho do dado.

---

## Quando usar Databricks

| Cenario | Databricks e ideal? |
|---|---|
| Volume > 100GB de dados | **Sim** — cluster distribui o processamento |
| Necessidade de time travel e ACID em data lake | **Sim** — Delta Lake resolve isso |
| Time de engenharia experiente em Spark | **Sim** — API madura e bem documentada |
| Volume < 10GB, budget limitado | **Nao** — PostgreSQL + dbt e mais simples e gratis |
| ML/AI sobre os dados transformados | **Sim** — MLflow, Feature Store integrados |
| Pipeline simples de ingestao | **Talvez** — Airflow pode ser suficiente |
