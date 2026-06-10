# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 03. Gold — Dimensoes
# MAGIC
# MAGIC Popula as 5 dimensoes do star schema em `banvic_gold`:
# MAGIC - `dim_tempo`       — calendario 2010-2026 enriquecido com Selic/CDI/PTAX/IPCA
# MAGIC - `dim_cliente`     — SCD Tipo 2 (snapshot corrente)
# MAGIC - `dim_agencia`     — agencias com lat/lon
# MAGIC - `dim_colaborador` — colaboradores com FK para dim_agencia
# MAGIC - `dim_canal`       — canais de atendimento derivados das transacoes

# COMMAND ----------

GOLD_PATH = "/FileStore/banvic/gold"

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from datetime import date, timedelta

def write_gold(df, table: str) -> None:
    (df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .option("path", f"{GOLD_PATH}/{table}")
     .saveAsTable(f"banvic_gold.{table}"))
    print(f"  OK  banvic_gold.{table:30s} {df.count():>10,} linhas")

# COMMAND ----------

# MAGIC %md ### dim_tempo — calendario diario 2010-2026

# COMMAND ----------

# Gerar sequencia de datas via Python (alternativa ao generate_series do PostgreSQL)
start_dt = date(2010, 1, 1)
end_dt   = date(2026, 12, 31)
dates    = [(start_dt + timedelta(days=i),)
            for i in range((end_dt - start_dt).days + 1)]

df_base = spark.createDataFrame(dates, ["data"])

# Carregar indicadores macroeconomicos
selic = (spark.table("banvic_bronze.selic")
         .select(F.col("data").cast("date").alias("selic_data"),
                 F.col("valor").cast("double").alias("taxa_selic")))

cdi = (spark.table("banvic_bronze.cdi")
       .select(F.col("data").cast("date").alias("cdi_data"),
               F.col("valor").cast("double").alias("taxa_cdi")))

ipca = (spark.table("banvic_bronze.ipca")
        .select(F.col("data").cast("date").alias("ipca_data"),
                F.col("valor").cast("double").alias("ipca_mensal"),
                F.col("acumulado_base_2010").cast("double").alias("ipca_acumulado")))

ptax = (spark.table("banvic_bronze.dolar_ptax")
        .select(F.col("data").cast("date").alias("ptax_data"),
                F.col("cotacao_venda").cast("double").alias("dolar_ptax")))

feriados = (spark.table("banvic_bronze.feriados")
            .select(F.col("data").cast("date").alias("feriado_data"),
                    F.col("descricao").alias("nome_feriado")))

# Construir dim_tempo com joins
dim_tempo = (df_base
    # Atributos calendarios
    .withColumn("sk_tempo",     F.row_number().over(Window.orderBy("data")).cast("integer"))
    .withColumn("ano",          F.year("data"))
    .withColumn("mes",          F.month("data"))
    .withColumn("dia",          F.dayofmonth("data"))
    .withColumn("trimestre",    F.quarter("data"))
    .withColumn("semana_ano",   F.weekofyear("data"))
    .withColumn("dia_semana",   F.dayofweek("data"))   # 1=dom, 7=sab
    .withColumn("nome_dia",     F.date_format("data", "EEEE"))
    .withColumn("nome_mes",     F.date_format("data", "MMMM"))
    .withColumn("ano_mes",      F.date_format("data", "yyyy-MM"))
    .withColumn("eh_fim_semana", F.dayofweek("data").isin([1, 7]))
    # Indicadores diarios
    .join(selic,  F.col("data") == F.col("selic_data"),  "left").drop("selic_data")
    .join(cdi,    F.col("data") == F.col("cdi_data"),    "left").drop("cdi_data")
    .join(ptax,   F.col("data") == F.col("ptax_data"),   "left").drop("ptax_data")
    # IPCA: dado mensal — join por ano+mes
    .join(ipca,
          (F.year("data")  == F.year("ipca_data")) &
          (F.month("data") == F.month("ipca_data")),
          "left").drop("ipca_data")
    # Feriados
    .join(feriados, F.col("data") == F.col("feriado_data"), "left").drop("feriado_data")
    .withColumn("eh_feriado",  F.col("nome_feriado").isNotNull())
    .withColumn("eh_dia_util", ~(F.col("eh_fim_semana") | F.col("eh_feriado")))
)
write_gold(dim_tempo, "dim_tempo")

# COMMAND ----------

# MAGIC %md ### dim_cliente — SCD Tipo 2 (snapshot corrente)

# COMMAND ----------

clientes = spark.table("banvic_silver.clientes")

dim_cliente = (clientes
    .withColumn("sk_cliente",           F.row_number().over(Window.orderBy("cod_cliente")).cast("integer"))
    .withColumn("data_inicio_vigencia", F.col("data_inclusao").cast("date"))
    .withColumn("data_fim_vigencia",    F.lit("9999-12-31").cast("date"))
    .withColumn("eh_registro_atual",    F.lit(True))
)
write_gold(dim_cliente, "dim_cliente")

# COMMAND ----------

# MAGIC %md ### dim_agencia

# COMMAND ----------

dim_agencia = (spark.table("banvic_silver.agencias")
    .withColumn("sk_agencia", F.row_number().over(Window.orderBy("cod_agencia")).cast("integer"))
)
write_gold(dim_agencia, "dim_agencia")

# COMMAND ----------

# MAGIC %md ### dim_colaborador

# COMMAND ----------

dim_ag_lookup = (spark.table("banvic_gold.dim_agencia")
                 .select("cod_agencia",
                         F.col("sk_agencia").alias("sk_agencia_principal")))

dim_colaborador = (spark.table("banvic_silver.colaboradores")
    .join(dim_ag_lookup, on="cod_agencia", how="left")
    .withColumn("sk_colaborador",
                F.row_number().over(Window.orderBy("cod_colaborador")).cast("integer"))
)
write_gold(dim_colaborador, "dim_colaborador")

# COMMAND ----------

# MAGIC %md ### dim_canal — derivada das transacoes

# COMMAND ----------

tipo_canal_expr = (
    F.when(F.col("nome_canal").isin("Internet Banking", "Aplicativo Movel"), "Digital")
     .when(F.col("nome_canal") == "Caixa Eletronico",   "Autoatendimento")
     .when(F.col("nome_canal") == "Agencia",            "Presencial")
     .when(F.col("nome_canal") == "Central Telefonica", "Remoto")
     .otherwise("Automatico")
)

dim_canal = (spark.table("banvic_silver.transacoes")
    .select(F.col("canal").alias("nome_canal"))
    .distinct()
    .withColumn("tipo_canal", tipo_canal_expr)
    .withColumn("sk_canal", F.row_number().over(Window.orderBy("nome_canal")).cast("integer"))
)
write_gold(dim_canal, "dim_canal")

# COMMAND ----------

print("Dimensoes Gold concluidas.")
spark.sql("SHOW TABLES IN banvic_gold").display()
