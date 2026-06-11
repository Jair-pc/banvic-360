# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 00. Setup
# MAGIC
# MAGIC Cria os databases no Hive Metastore, define os caminhos DBFS e valida
# MAGIC que os CSVs foram carregados antes de iniciar o pipeline.
# MAGIC
# MAGIC **Execute uma unica vez antes dos demais notebooks.**

# COMMAND ----------

BASE_PATH   = "/Volumes/workspace/banvic/data"
CSV_BANVIC  = f"{BASE_PATH}/banvic"
CSV_SINT    = f"{BASE_PATH}/sintetico"
CSV_EXT     = f"{BASE_PATH}/external_data"
BRONZE_PATH = f"{BASE_PATH}/bronze"
SILVER_PATH = f"{BASE_PATH}/silver"
GOLD_PATH   = f"{BASE_PATH}/gold"

# Compartilhar com demais notebooks via dbutils
dbutils.widgets.text("base_path", BASE_PATH)

# COMMAND ----------

for db in ("banvic_bronze", "banvic_silver", "banvic_gold"):
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db}")
    print(f"OK: database {db}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upload dos CSVs para o DBFS
# MAGIC
# MAGIC Os dados devem estar no DBFS **antes** de rodar o pipeline.
# MAGIC Os arquivos ficam fora do git (apenas no Drive/DBFS).
# MAGIC
# MAGIC ### Opcao 1 — Databricks CLI
# MAGIC ```bash
# MAGIC pip install databricks-cli
# MAGIC databricks configure --token
# MAGIC
# MAGIC databricks fs mkdirs dbfs:/FileStore/banvic/csv
# MAGIC databricks fs cp -r data/banvic/      dbfs:/FileStore/banvic/csv/banvic/
# MAGIC databricks fs cp -r data/sintetico/   dbfs:/FileStore/banvic/csv/sintetico/
# MAGIC databricks fs cp -r external_data/    dbfs:/FileStore/banvic/csv/external_data/
# MAGIC ```
# MAGIC
# MAGIC ### Opcao 2 — UI (Community Edition)
# MAGIC **Data** -> **Add Data** -> **DBFS** -> `/FileStore/banvic/csv/`

# COMMAND ----------

# Verificar presenca dos arquivos essenciais
arquivos_esperados = [
    (f"{CSV_BANVIC}/clientes.csv",              "clientes"),
    (f"{CSV_BANVIC}/contas.csv",                "contas"),
    (f"{CSV_BANVIC}/transacoes.csv",            "transacoes"),
    (f"{CSV_BANVIC}/agencias.csv",              "agencias"),
    (f"{CSV_BANVIC}/colaboradores.csv",         "colaboradores"),
    (f"{CSV_BANVIC}/propostas_credito.csv",     "propostas_credito"),
    (f"{CSV_SINT}/clientes_sinteticos.csv",     "clientes_sinteticos"),
    (f"{CSV_SINT}/contas_sinteticas.csv",       "contas_sinteticas"),
    (f"{CSV_SINT}/transacoes_sinteticas.csv",   "transacoes_sinteticas"),
    (f"{CSV_EXT}/macroeconomia/selic.csv",      "selic"),
    (f"{CSV_EXT}/macroeconomia/ipca.csv",       "ipca"),
]

ok, faltando = 0, 0
for path, nome in arquivos_esperados:
    try:
        dbutils.fs.ls(path)
        print(f"  OK    {nome}")
        ok += 1
    except Exception:
        print(f"  FALTA {path}")
        faltando += 1

print(f"\n{ok}/{len(arquivos_esperados)} arquivos encontrados.")
if faltando > 0:
    raise Exception(f"{faltando} arquivo(s) faltando. Faca o upload antes de continuar.")

# COMMAND ----------

print("Setup concluido. Ordem de execucao:")
print("  01_bronze.py      -> CSV -> Delta Bronze (35 tabelas)")
print("  02_silver.py      -> Bronze -> Silver (DQ + tipagem)")
print("  03_gold_dims.py   -> Silver -> Gold (5 dimensoes)")
print("  04_gold_fatos.py  -> Silver -> Gold (3 fatos)")
print("  05_validar_kpis.py -> 8 KPIs vs gabarito")
