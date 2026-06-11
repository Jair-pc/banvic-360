# Projeto 7 — Databricks Lakehouse

Este projeto faz o mesmo pipeline do BanVic usando **PySpark + Delta Lake no Databricks** — a plataforma usada quando os dados são grandes demais para caber em uma só máquina.

**Pergunta principal:** _O que muda quando o dado não cabe mais em uma máquina?_

---

## O problema que o Databricks resolve

Os projetos anteriores rodam no seu computador: o banco fica local, o Python processa localmente. Isso funciona para o BanVic (70k transações), mas um banco real pode ter 100 milhões de transações por dia.

O Databricks distribui o processamento em vários computadores ao mesmo tempo (cluster). Os dados ficam em **Delta Lake** — um formato de arquivo que tem as vantagens de um banco de dados (ACID, histórico de versões) com as vantagens de um data lake (barato, escala infinita).

---

## Resultado

```
8/8 KPIs corretos — APROVADO
```

---

## Arquivos do projeto

```
projetos/07-databricks/
├── notebooks/
│   ├── 00_setup.py          Cria os databases, verifica os CSVs no DBFS
│   ├── 01_bronze.py         CSV → Delta Bronze (35 tabelas + compactação)
│   ├── 02_silver.py         Bronze → Silver (limpeza + tipagem + união real+sintético)
│   ├── 03_gold_dims.py      Silver → Dimensões Gold (5 dimensões + dim_tempo)
│   ├── 04_gold_fatos.py     Silver → Fatos Gold (3 tabelas fato)
│   └── 05_validar_kpis.py   8 KPIs via Spark SQL + comparação com gabarito
├── dlt/
│   └── banvic_pipeline_dlt.py  Versão alternativa usando Delta Live Tables
├── job_config.json          Configuração do Job Databricks (agendamento automático)
├── prints/                  Screenshots da execução no Databricks
├── run.bat                  Windows: importa notebooks + cria job via CLI
└── run.sh                   Linux/Mac: idem
```

---

## Como executar

### Pré-requisito: subir os CSVs para o Databricks

Os dados ficam fora do git. Você precisa carregá-los no DBFS (sistema de arquivos do Databricks).

**Opção 1 — pela interface visual (mais fácil):**
1. No Databricks: menu **Catalog** → **Add data** → **Upload files**
2. Destino: `/FileStore/banvic/csv/banvic/` para os dados originais
3. Destino: `/FileStore/banvic/csv/sintetico/` para os sintéticos
4. Destino: `/FileStore/banvic/csv/external_data/` para os dados externos

**Opção 2 — pela linha de comando:**
```bash
pip install databricks-cli
databricks configure --token

databricks fs mkdirs dbfs:/FileStore/banvic/csv
databricks fs cp -r data/banvic/      dbfs:/FileStore/banvic/csv/banvic/
databricks fs cp -r data/sintetico/   dbfs:/FileStore/banvic/csv/sintetico/
databricks fs cp -r external_data/    dbfs:/FileStore/banvic/csv/external_data/
```

### Passo a passo no Databricks Community Edition (gratuito)

1. **Criar cluster:** Compute → Create Cluster → Single Node → DBR 14.3 LTS
2. **Importar notebooks:** Workspace → Import → selecionar cada arquivo `.py`
3. **Executar em ordem:** `00_setup` → `01_bronze` → `02_silver` → `03_gold_dims` → `04_gold_fatos` → `05_validar_kpis`

### Executar via CLI (conta paga)

```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh && ./run.sh
```

### Testar localmente (sem Databricks)

```bash
pip install pyspark==3.5.1 delta-spark==3.2.0
# Ajustar: remover dbutils, trocar display() por show(), ajustar caminhos
python notebooks/02_silver.py
```

---

## O que é Delta Lake

Delta Lake é um formato de armazenamento que funciona em cima de arquivos Parquet e adiciona:

- **ACID**: transações seguras — ou salva tudo, ou não salva nada
- **Time Travel**: você pode consultar como a tabela estava ontem, ou na versão 3
- **Schema enforcement**: rejeita automaticamente dados com formato errado
- **OPTIMIZE**: consolida arquivos pequenos em arquivos maiores (mais rápido para ler)

Exemplo de time travel:
```python
# Como estava a tabela antes de qualquer mudança
spark.read.format("delta").option("versionAsOf", 0).table("banvic_bronze.transacoes")

# Ver o histórico completo de mudanças
spark.sql("DESCRIBE HISTORY banvic_bronze.transacoes").show()
```

---

## Delta Live Tables — a abordagem declarativa

O arquivo `dlt/banvic_pipeline_dlt.py` mostra uma abordagem diferente: em vez de dizer **como** processar, você diz **o que** a tabela precisa conter. O Databricks cuida do resto.

```python
@dlt.table(name="silver_clientes")
@dlt.expect_or_fail("cod_cliente nao nulo", "cod_cliente IS NOT NULL")
def silver_clientes():
    # Só descreve o que a tabela deve ter
    return spark.read.table("banvic_bronze.clientes")
```

| | Notebooks manuais | Delta Live Tables |
|---|---|---|
| Ordem de execução | Você define | Automática |
| Retry em caso de falha | Configurar no Job | Embutido |
| Monitoramento de qualidade | Manual | Dashboard automático |
| Rastreabilidade dos dados | Nenhuma | Grafo interativo |
| Disponível no Community Edition | Sim | Não (requer plano pago) |

---

## Resultados da execução

### Três schemas criados (Bronze / Silver / Gold)

![Catalog Explorer](prints/Catalog%20Explorer.png)

> `banvic_bronze`, `banvic_silver` e `banvic_gold` no Unity Catalog com 35 tabelas Delta.

### Bronze — 25 tabelas Delta carregadas

![Output 01_bronze](prints/Output%20do%2001_bronze.png)

### Silver — 6 tabelas transformadas

![Output 02_silver](prints/Output%20do%2002_silver.png)

### Validação — 8/8 KPIs aprovados

![Resumo final](prints/resumo_final.png)

> KPI1: saldo R$ 26.509.620,12 — exatamente o gabarito. Zero divergência.

---

## Databricks vs os outros projetos

| O que você precisa | SQL / Python / Airflow / dbt | Databricks |
|---|---|---|
| Volume de dados | Limitado à memória do servidor | Petabytes (cluster distribuído) |
| Histórico e auditoria de dados | Não | Sim — Delta Time Travel |
| Processamento em paralelo | Não ou limitado | Sim — cluster Spark |
| Transações ACID em arquivos | Não | Sim — Delta Lake |
| Integração com Machine Learning | Limitada | Nativa — MLflow, Feature Store |
| Custo | Gratuito (local) | Pago (cloud) |

---

## Quando usar Databricks

| Situação | Faz sentido? |
|---|---|
| Volume acima de 100 GB de dados | Sim — cluster distribui o processamento |
| Precisar de time travel e ACID em data lake | Sim — Delta Lake resolve isso |
| Machine Learning sobre os dados transformados | Sim — MLflow integrado |
| Volume abaixo de 10 GB, budget limitado | Não — PostgreSQL + dbt é mais simples e gratuito |
| Pipeline simples de ingestão | Talvez — Airflow pode ser suficiente |
