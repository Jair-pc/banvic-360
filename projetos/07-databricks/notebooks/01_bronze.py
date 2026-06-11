# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 01. Bronze
# MAGIC
# MAGIC Ingestao bruta: CSVs -> Delta Lake (`banvic_bronze`).
# MAGIC Sem transformacao — os dados chegam como no arquivo original.
# MAGIC
# MAGIC **Delta Lake garante:** ACID, time travel, schema enforcement, compactacao automatica.

# COMMAND ----------

BASE_PATH   = "/Volumes/workspace/banvic/data"
CSV_BANVIC  = f"{BASE_PATH}/banvic"
CSV_SINT    = f"{BASE_PATH}/sintetico"
CSV_EXT     = f"{BASE_PATH}/external_data"
BRONZE_PATH = f"{BASE_PATH}/bronze"

# COMMAND ----------

def load_csv(path: str, table: str, sep: str = ",") -> int:
    """Le CSV e grava como Delta table em banvic_bronze."""
    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .option("sep", sep)
          .option("encoding", "UTF-8")
          .csv(path))

    (df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .saveAsTable(f"banvic_bronze.{table}"))

    n = df.count()
    print(f"  OK  banvic_bronze.{table:40s} {n:>10,} linhas")
    return n

# COMMAND ----------

# MAGIC %md ### Dados originais BanVic

# COMMAND ----------

total = 0
total += load_csv(f"{CSV_BANVIC}/clientes.csv",          "clientes")
total += load_csv(f"{CSV_BANVIC}/contas.csv",            "contas")
total += load_csv(f"{CSV_BANVIC}/transacoes.csv",        "transacoes")
total += load_csv(f"{CSV_BANVIC}/agencias.csv",          "agencias")
total += load_csv(f"{CSV_BANVIC}/colaboradores.csv",     "colaboradores")
total += load_csv(f"{CSV_BANVIC}/propostas_credito.csv", "propostas_credito")

# COMMAND ----------

# MAGIC %md ### Dados sinteticos

# COMMAND ----------

total += load_csv(f"{CSV_SINT}/clientes_sinteticos.csv",      "clientes_sinteticos")
total += load_csv(f"{CSV_SINT}/contas_sinteticas.csv",        "contas_sinteticas")
total += load_csv(f"{CSV_SINT}/transacoes_sinteticas.csv",    "transacoes_sinteticas")
total += load_csv(f"{CSV_SINT}/propostas_sinteticas.csv",     "propostas_sinteticas")
total += load_csv(f"{CSV_SINT}/agencias_expandidas.csv",      "agencias_expandidas")
total += load_csv(f"{CSV_SINT}/colaboradores_expandidos.csv", "colaboradores_expandidos")
total += load_csv(f"{CSV_SINT}/investimentos.csv",            "investimentos")
total += load_csv(f"{CSV_SINT}/seguros.csv",                  "seguros")
total += load_csv(f"{CSV_SINT}/cartoes.csv",                  "cartoes")
total += load_csv(f"{CSV_SINT}/inadimplencia.csv",            "inadimplencia")
total += load_csv(f"{CSV_SINT}/fraudes.csv",                  "fraudes")

# COMMAND ----------

# MAGIC %md ### Dados externos (macroeconomia + geografia)

# COMMAND ----------

total += load_csv(f"{CSV_EXT}/macroeconomia/selic.csv",          "selic")
total += load_csv(f"{CSV_EXT}/macroeconomia/cdi.csv",            "cdi")
total += load_csv(f"{CSV_EXT}/macroeconomia/ipca.csv",           "ipca")
total += load_csv(f"{CSV_EXT}/macroeconomia/dolar_ptax.csv",     "dolar_ptax")
total += load_csv(f"{CSV_EXT}/macroeconomia/euro_ptax.csv",      "euro_ptax")
total += load_csv(f"{CSV_EXT}/macroeconomia/desemprego.csv",     "desemprego")
total += load_csv(f"{CSV_EXT}/geografia/municipios.csv",         "municipios_ibge")
total += load_csv(f"{CSV_EXT}/calendario/feriados.csv",          "feriados")

print(f"\nTotal Bronze: {total:,} linhas em todas as tabelas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Delta Lake: Time Travel
# MAGIC
# MAGIC Delta registra o historico de cada tabela. E possivel consultar versoes anteriores:
# MAGIC
# MAGIC ```python
# MAGIC # Por versao
# MAGIC spark.read.format("delta").option("versionAsOf", 0).table("banvic_bronze.transacoes")
# MAGIC
# MAGIC # Por timestamp
# MAGIC spark.read.format("delta").option("timestampAsOf", "2024-01-01").table("banvic_bronze.transacoes")
# MAGIC
# MAGIC # Ver historico completo
# MAGIC spark.sql("DESCRIBE HISTORY banvic_bronze.transacoes").display()
# MAGIC ```

# COMMAND ----------

# MAGIC %md ## Compactacao (melhora leitura de tabelas grandes)

# COMMAND ----------

# OPTIMIZE consolida small files — especifico do Databricks (Delta OSS usa Python API)
for t in ("transacoes", "transacoes_sinteticas", "cartoes", "contas_sinteticas"):
    spark.sql(f"OPTIMIZE banvic_bronze.{t}")
    print(f"  OK  OPTIMIZE banvic_bronze.{t}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resumo do schema Bronze
# MAGIC
# MAGIC Bronze preserva os tipos originais do CSV (inferSchema). A camada Silver e
# MAGIC responsavel por tipar, limpar e padronizar.

# COMMAND ----------

spark.sql("SHOW TABLES IN banvic_bronze").display()
