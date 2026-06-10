# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — Delta Live Tables (DLT)
# MAGIC
# MAGIC Versao declarativa do pipeline usando Delta Live Tables.
# MAGIC
# MAGIC **Diferenca vs notebooks manuais:**
# MAGIC - Voce define O QUE cada tabela deve conter
# MAGIC - A plataforma resolve a ordem de execucao, retries e monitoramento
# MAGIC - `@dlt.expect_or_fail` substitui validacoes manuais de DQ
# MAGIC
# MAGIC **Como usar:**
# MAGIC 1. Engenharia de Dados -> Pipelines -> Criar pipeline
# MAGIC 2. Tipo: Delta Live Tables
# MAGIC 3. Notebook: apontar para este arquivo
# MAGIC 4. Storage: `/FileStore/banvic/dlt`
# MAGIC
# MAGIC **Nota:** DLT requer plano Premium ou superior (nao disponivel no Community Edition).

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

BASE_PATH  = "/FileStore/banvic"
CSV_BANVIC = f"{BASE_PATH}/csv/banvic"
CSV_SINT   = f"{BASE_PATH}/csv/sintetico"

# COMMAND ----------

# MAGIC %md ## Bronze — Ingestao declarativa

# COMMAND ----------

@dlt.table(name="bronze_clientes", comment="Clientes originais do BanVic (998 registros)")
def bronze_clientes():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_BANVIC}/clientes.csv"))

@dlt.table(name="bronze_clientes_sinteticos", comment="Clientes sinteticos (50k registros)")
def bronze_clientes_sinteticos():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_SINT}/clientes_sinteticos.csv"))

@dlt.table(name="bronze_contas")
def bronze_contas():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_BANVIC}/contas.csv"))

@dlt.table(name="bronze_contas_sinteticas")
def bronze_contas_sinteticas():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_SINT}/contas_sinteticas.csv"))

@dlt.table(name="bronze_transacoes")
def bronze_transacoes():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_BANVIC}/transacoes.csv"))

@dlt.table(name="bronze_transacoes_sinteticas")
def bronze_transacoes_sinteticas():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_SINT}/transacoes_sinteticas.csv"))

@dlt.table(name="bronze_propostas_credito", comment="Propostas originais — grain do gabarito")
def bronze_propostas_credito():
    return (spark.read
            .option("header", True).option("inferSchema", True)
            .csv(f"{CSV_BANVIC}/propostas_credito.csv"))

# COMMAND ----------

# MAGIC %md ## Silver — Transformacao + Data Quality

# COMMAND ----------

@dlt.table(
    name="silver_clientes",
    comment="Clientes limpos: real + sintetico, deduplicados por cod_cliente"
)
@dlt.expect_or_fail("cod_cliente nao nulo",    "cod_cliente IS NOT NULL")
@dlt.expect(       "cpf formato valido",        "LENGTH(cpf) = 14")
@dlt.expect(       "renda positiva",            "renda_mensal > 0")
def silver_clientes():
    cols = ["cod_cliente", "nome", "cpf", "data_nascimento", "sexo",
            "cidade", "estado", "cod_agencia", "renda_mensal",
            "score_credito", "segmento", "data_inclusao"]

    real = dlt.read("bronze_clientes").select(cols)
    sint = dlt.read("bronze_clientes_sinteticos").select(cols)

    w = Window.partitionBy("cod_cliente").orderBy(F.desc("data_inclusao"))
    return (real.union(sint)
        .withColumn("_rn", F.row_number().over(w))
        .filter("_rn = 1").drop("_rn")
        .withColumn("data_nascimento", F.col("data_nascimento").cast("date"))
        .withColumn("renda_mensal",    F.col("renda_mensal").cast("double"))
        .withColumn("score_credito",   F.col("score_credito").cast("integer"))
        .withColumn("faixa_etaria",
            F.when(F.datediff(F.current_date(), F.col("data_nascimento")) / 365.25 < 25,  "18-24")
             .when(F.datediff(F.current_date(), F.col("data_nascimento")) / 365.25 < 35,  "25-34")
             .when(F.datediff(F.current_date(), F.col("data_nascimento")) / 365.25 < 45,  "35-44")
             .when(F.datediff(F.current_date(), F.col("data_nascimento")) / 365.25 < 55,  "45-54")
             .when(F.datediff(F.current_date(), F.col("data_nascimento")) / 365.25 < 65,  "55-64")
             .otherwise("65+")))

@dlt.table(name="silver_contas")
@dlt.expect_or_fail("num_conta nao nulo", "num_conta IS NOT NULL")
@dlt.expect(        "saldo nao negativo",  "saldo_total >= 0")
def silver_contas():
    todas = (dlt.read("bronze_contas")
             .union(dlt.read("bronze_contas_sinteticas")))
    max_date = todas.agg(F.max("data_ultimo_lancamento")).collect()[0][0]
    return (todas
        .withColumn("data_abertura",          F.col("data_abertura").cast("date"))
        .withColumn("data_ultimo_lancamento", F.col("data_ultimo_lancamento").cast("date"))
        .withColumn("saldo_total",            F.col("saldo_total").cast("double"))
        .withColumn("limite_credito",         F.col("limite_credito").cast("double"))
        .withColumn("eh_conta_ativa",
            F.col("data_ultimo_lancamento") >=
            F.date_sub(F.lit(max_date).cast("date"), 90)))

@dlt.table(name="silver_propostas")
def silver_propostas():
    return (dlt.read("bronze_propostas_credito")
        .withColumn("data_proposta",  F.col("data_proposta").cast("date"))
        .withColumn("valor_proposta", F.col("valor_proposta").cast("double")))

# COMMAND ----------

# MAGIC %md ## Gold — Modelo Dimensional

# COMMAND ----------

@dlt.table(name="gold_dim_agencia", comment="Agencias com SK surrogate")
def gold_dim_agencia():
    return (spark.table("banvic_bronze.agencias")
        .withColumn("sk_agencia",
                    F.row_number().over(Window.orderBy("cod_agencia")).cast("integer")))

@dlt.table(
    name="gold_fato_contas",
    comment="Snapshot corrente: 1 linha por conta, todas as contas ativas"
)
def gold_fato_contas():
    contas  = dlt.read("silver_contas")
    dim_ag  = dlt.read("gold_dim_agencia").select("cod_agencia", "sk_agencia")
    return (contas
        .join(dim_ag, on="cod_agencia", how="left")
        .select("num_conta", "cod_cliente", "cod_agencia", "tipo_conta",
                "saldo_total", "limite_credito", "eh_conta_ativa", "sk_agencia"))

@dlt.table(
    name="gold_fato_propostas_credito",
    comment="Propostas originais (grain gabarito: 1.996 linhas)"
)
def gold_fato_propostas_credito():
    # Le Bronze diretamente para manter grain consistente com o gabarito
    return (dlt.read("bronze_propostas_credito")
        .withColumn("data_proposta",  F.col("data_proposta").cast("date"))
        .withColumn("valor_proposta", F.col("valor_proposta").cast("double")))
