# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 04. Gold — Fatos
# MAGIC
# MAGIC Popula as 3 tabelas fato do star schema:
# MAGIC - `fato_contas`            — snapshot corrente (1 linha por conta)
# MAGIC - `fato_transacoes`        — todas as transacoes com FKs para dims
# MAGIC - `fato_propostas_credito` — propostas do dataset **original** (grain do gabarito)

# COMMAND ----------

GOLD_PATH = "/Volumes/workspace/banvic/data/gold"

from pyspark.sql import functions as F
from pyspark.sql.window import Window

def write_gold(df, table: str) -> None:
    (df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .saveAsTable(f"banvic_gold.{table}"))
    print(f"  OK  banvic_gold.{table:30s} {df.count():>10,} linhas")

# COMMAND ----------

# Carregar dimensoes para lookup (broadcast para joins eficientes)
from pyspark.sql.functions import broadcast

dim_tempo   = broadcast(spark.table("banvic_gold.dim_tempo")
                        .select("sk_tempo", F.col("data").alias("dim_data")))
dim_cliente = broadcast(spark.table("banvic_gold.dim_cliente")
                        .filter("eh_registro_atual = true")
                        .select("sk_cliente", "cod_cliente"))
dim_agencia = broadcast(spark.table("banvic_gold.dim_agencia")
                        .select("sk_agencia", "cod_agencia"))
dim_colab   = broadcast(spark.table("banvic_gold.dim_colaborador")
                        .select("sk_colaborador", "cod_colaborador"))
dim_canal   = broadcast(spark.table("banvic_gold.dim_canal")
                        .select("sk_canal", "nome_canal"))

# COMMAND ----------

# MAGIC %md ### fato_contas — snapshot corrente (grain: 1 linha por conta)

# COMMAND ----------

contas = spark.table("banvic_silver.contas")

fato_contas = (contas
    .join(dim_agencia, on="cod_agencia", how="left")
    .join(dim_cliente, on="cod_cliente", how="left")
    .join(dim_colab,   on="cod_colaborador", how="left")
    .join(dim_tempo.withColumnRenamed("dim_data", "data_abertura_join"),
          F.col("data_abertura") == F.col("data_abertura_join"), "left")
    .withColumnRenamed("sk_tempo", "sk_tempo_abertura")
    .drop("data_abertura_join")
    .select(
        "num_conta", "cod_cliente", "cod_agencia", "cod_colaborador",
        "tipo_conta", "saldo_total",
        "data_abertura", "data_ultimo_lancamento", "eh_conta_ativa",
        "sk_cliente", "sk_agencia", "sk_colaborador", "sk_tempo_abertura"
    )
)
write_gold(fato_contas, "fato_contas")

# COMMAND ----------

# MAGIC %md ### fato_transacoes

# COMMAND ----------

transacoes = spark.table("banvic_silver.transacoes")
# Precisamos do cod_agencia e cod_cliente via contas Silver
contas_lookup = (spark.table("banvic_silver.contas")
                 .select("num_conta", "cod_agencia", "cod_cliente"))

fato_transacoes = (transacoes
    .join(contas_lookup, on="num_conta", how="left")
    .join(dim_tempo.withColumnRenamed("dim_data", "data_tx"),
          F.col("data_transacao") == F.col("data_tx"), "left").drop("data_tx")
    .join(dim_cliente, on="cod_cliente", how="left")
    .join(dim_agencia, on="cod_agencia", how="left")
    .join(dim_canal.withColumnRenamed("nome_canal", "canal_dim"),
          F.col("canal") == F.col("canal_dim"), "left").drop("canal_dim")
    .select(
        "cod_transacao", "num_conta", "data_transacao",
        "nome_transacao", "valor_transacao", "canal",
        "sk_tempo", "sk_cliente", "sk_agencia", "sk_canal"
    )
)
write_gold(fato_transacoes, "fato_transacoes")

# COMMAND ----------

# MAGIC %md
# MAGIC ### fato_propostas_credito
# MAGIC
# MAGIC **Importante:** le diretamente do Bronze (`propostas_credito` original),
# MAGIC nao do Silver. Isso mantem o grain de 1.996 linhas consistente com o gabarito.
# MAGIC O Silver une real + sintetico — seria um grain diferente.

# COMMAND ----------

propostas = (spark.table("banvic_bronze.propostas_credito")
    .withColumnRenamed("data_entrada_proposta", "data_proposta")
    .withColumnRenamed("taxa_juros_mensal",      "taxa_juros")
    .withColumnRenamed("quantidade_parcelas",    "prazo_meses"))

fato_propostas = (propostas
    .withColumn("data_proposta",  F.col("data_proposta").cast("date"))
    .withColumn("valor_proposta", F.col("valor_proposta").cast("double"))
    .withColumn("taxa_juros",     F.col("taxa_juros").cast("double"))
    .withColumn("prazo_meses",    F.col("prazo_meses").cast("integer"))
    .join(dim_tempo.withColumnRenamed("dim_data", "data_prop_join"),
          F.col("data_proposta") == F.col("data_prop_join"), "left").drop("data_prop_join")
    .join(dim_cliente, on="cod_cliente",   how="left")
    .join(dim_colab,   on="cod_colaborador", how="left")
    .select(
        "cod_proposta", "cod_cliente", "cod_colaborador",
        "data_proposta", "valor_proposta", "status_proposta",
        "prazo_meses", "taxa_juros",
        "sk_tempo", "sk_cliente", "sk_colaborador"
    )
)
write_gold(fato_propostas, "fato_propostas_credito")

# COMMAND ----------

print("Fatos Gold concluidos.")
spark.sql("""
    SELECT table_name,
           (SELECT COUNT(*) FROM banvic_gold.fato_transacoes)   AS fato_transacoes,
           (SELECT COUNT(*) FROM banvic_gold.fato_contas)        AS fato_contas,
           (SELECT COUNT(*) FROM banvic_gold.fato_propostas_credito) AS fato_propostas
    FROM information_schema.tables
    WHERE table_schema = 'banvic_gold' AND table_name LIKE 'fato_%'
    LIMIT 1
""").display()
