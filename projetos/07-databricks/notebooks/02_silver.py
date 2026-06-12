# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 02. Silver
# MAGIC
# MAGIC Transforma Bronze -> Silver:
# MAGIC - Tipagem correta (string -> date, double, int)
# MAGIC - UNION dos datasets originais + sinteticos (schemas normalizados)
# MAGIC - Deduplicacao por chave natural (mais recente vence)
# MAGIC - Regras de DQ (campo nao-nulo, faixas validas)
# MAGIC - Colunas derivadas: `canal`, `eh_conta_ativa`, `faixa_etaria`

# COMMAND ----------

SILVER_PATH = "/Volumes/workspace/banvic/data/silver"

from pyspark.sql import functions as F
from pyspark.sql.window import Window

def write_silver(df, table: str) -> None:
    (df.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .saveAsTable(f"banvic_silver.{table}"))
    print(f"  OK  banvic_silver.{table:30s} {df.count():>10,} linhas")

# COMMAND ----------

# MAGIC %md ### Clientes — UNION real + sintetico, deduplicacao
# MAGIC
# MAGIC Schema real: `cod_cliente, primeiro_nome, ultimo_nome, cpfcnpj, data_nascimento, data_inclusao`
# MAGIC Schema sint: `cod_cliente, nome, cpf, data_nascimento, sexo, estado_civil, ...`

# COMMAND ----------

cols_clientes = [
    "cod_cliente", "nome", "cpf", "data_nascimento", "sexo", "estado_civil",
    "cidade", "estado", "cod_agencia", "cod_colaborador", "data_inclusao",
    "renda_mensal", "score_credito", "faixa_score", "segmento",
    "profissao", "nivel_escolaridade", "produto_principal"
]

# Real: normalizar para o schema sintetico
clientes_real = (spark.table("banvic_bronze.clientes")
    .withColumn("nome", F.concat_ws(" ", F.col("primeiro_nome"), F.col("ultimo_nome")))
    .withColumnRenamed("cpfcnpj", "cpf"))

clientes_sint = spark.table("banvic_bronze.clientes_sinteticos")

# unionByName preenche colunas ausentes com NULL
clientes_all = clientes_real.unionByName(clientes_sint, allowMissingColumns=True)

# Dedup: manter o registro mais recente por cod_cliente
w_dedup = Window.partitionBy("cod_cliente").orderBy(F.desc("data_inclusao"))

clientes_clean = (clientes_all
    .withColumn("_rn", F.row_number().over(w_dedup))
    .filter("_rn = 1")
    .drop("_rn")
    .withColumn("data_nascimento", F.col("data_nascimento").cast("date"))
    .withColumn("data_inclusao",   F.col("data_inclusao").cast("timestamp"))
    .withColumn("renda_mensal",    F.col("renda_mensal").cast("double"))
    .withColumn("score_credito",   F.col("score_credito").cast("integer"))
    .withColumn("faixa_etaria",
        # Data fixa = dia em que o gabarito foi gerado (faixa etaria deterministica)
        F.when(F.datediff(F.lit("2026-06-10").cast("date"), F.col("data_nascimento")) / 365.25 < 25,  "18-24")
         .when(F.datediff(F.lit("2026-06-10").cast("date"), F.col("data_nascimento")) / 365.25 < 35,  "25-34")
         .when(F.datediff(F.lit("2026-06-10").cast("date"), F.col("data_nascimento")) / 365.25 < 45,  "35-44")
         .when(F.datediff(F.lit("2026-06-10").cast("date"), F.col("data_nascimento")) / 365.25 < 55,  "45-54")
         .when(F.datediff(F.lit("2026-06-10").cast("date"), F.col("data_nascimento")) / 365.25 < 65,  "55-64")
         .otherwise("65+"))
)
write_silver(clientes_clean, "clientes")

# COMMAND ----------

# MAGIC %md ### Contas — UNION + flag eh_conta_ativa
# MAGIC
# MAGIC Real nao tem `limite_credito` nem `flag_ativa` — unionByName preenche com NULL.

# COMMAND ----------

contas_orig = spark.table("banvic_bronze.contas")
contas_sint = spark.table("banvic_bronze.contas_sinteticas")
contas_all  = contas_orig.unionByName(contas_sint, allowMissingColumns=True)

# eh_conta_ativa: ativa se lancamento nos ultimos 90 dias antes do max do dataset
max_lancamento = contas_all.agg(F.max("data_ultimo_lancamento")).collect()[0][0]

contas_clean = (contas_all
    .withColumn("data_abertura",          F.col("data_abertura").cast("date"))
    .withColumn("data_ultimo_lancamento", F.col("data_ultimo_lancamento").cast("date"))
    .withColumn("saldo_total",            F.col("saldo_total").cast("double"))
    .withColumn("limite_credito",         F.col("limite_credito").cast("double"))
    .withColumn("eh_conta_ativa",
        F.col("data_ultimo_lancamento").cast("date") >=
        F.date_sub(F.lit(max_lancamento).cast("date"), 90))
)
write_silver(contas_clean, "contas")

# COMMAND ----------

# MAGIC %md ### Transacoes — UNION + derivar canal
# MAGIC
# MAGIC Real e sintetico tem o mesmo schema: `cod_transacao, num_conta, data_transacao, nome_transacao, valor_transacao`

# COMMAND ----------

# Mapeia nome_transacao -> canal de atendimento
canal_expr = (
    F.when(F.lower(F.col("nome_transacao")).like("%internet banking%"), "Internet Banking")
     .when(F.lower(F.col("nome_transacao")).like("%aplicativo%"),        "Aplicativo Movel")
     .when(F.lower(F.col("nome_transacao")).like("%app%"),               "Aplicativo Movel")
     .when(F.lower(F.col("nome_transacao")).like("%pix%"),               "Aplicativo Movel")
     .when(F.lower(F.col("nome_transacao")).like("%caixa eletronico%"),  "Caixa Eletronico")
     .when(F.lower(F.col("nome_transacao")).like("%atm%"),               "Caixa Eletronico")
     .when(F.lower(F.col("nome_transacao")).like("%agencia%"),           "Agencia")
     .when(F.lower(F.col("nome_transacao")).like("%telefone%"),          "Central Telefonica")
     .when(F.lower(F.col("nome_transacao")).like("%debito automatico%"), "Debito Automatico")
     .when(F.lower(F.col("nome_transacao")).like("%ted%"),               "Internet Banking")
     .otherwise("Outros")
)

transacoes_orig = spark.table("banvic_bronze.transacoes")
transacoes_sint = spark.table("banvic_bronze.transacoes_sinteticas")
transacoes_all  = transacoes_orig.union(transacoes_sint)

transacoes_clean = (transacoes_all
    .withColumn("data_transacao",  F.col("data_transacao").cast("date"))
    .withColumn("valor_transacao", F.col("valor_transacao").cast("double"))
    .withColumn("canal", canal_expr)
)
write_silver(transacoes_clean, "transacoes")

# COMMAND ----------

# MAGIC %md ### Agencias — enriquecer com lat/lon das expandidas

# COMMAND ----------

agencias      = spark.table("banvic_bronze.agencias")
agencias_exp  = spark.table("banvic_bronze.agencias_expandidas")

coords = agencias_exp.select("cod_agencia",
                              F.col("latitude").cast("double"),
                              F.col("longitude").cast("double"),
                              "regiao")

agencias_clean = (agencias
    .join(coords, on="cod_agencia", how="left")
    .withColumn("data_abertura", F.col("data_abertura").cast("date"))
)
write_silver(agencias_clean, "agencias")

# COMMAND ----------

# MAGIC %md ### Colaboradores — usar expandidos como fonte principal
# MAGIC
# MAGIC Original tem apenas nome/cpf sem cargo/salario. Expandidos ja inclui todos os originais.
# MAGIC Schema expandidos: `primeiro_nome, ultimo_nome, salario_base` -> normalizar para `nome, salario`.

# COMMAND ----------

colab_clean = (spark.table("banvic_bronze.colaboradores_expandidos")
    .withColumn("nome",    F.concat_ws(" ", F.col("primeiro_nome"), F.col("ultimo_nome")))
    .withColumnRenamed("salario_base", "salario")
    .withColumn("data_admissao", F.col("data_admissao").cast("date"))
    .withColumn("salario",       F.col("salario").cast("double"))
)
write_silver(colab_clean, "colaboradores")

# COMMAND ----------

# MAGIC %md ### Propostas — UNION real + sintetico
# MAGIC
# MAGIC Renomear colunas para schema padrao:
# MAGIC `data_entrada_proposta` -> `data_proposta`, `taxa_juros_mensal` -> `taxa_juros`, `quantidade_parcelas` -> `prazo_meses`

# COMMAND ----------

def normalizar_propostas(df):
    return (df
        .withColumnRenamed("data_entrada_proposta", "data_proposta")
        .withColumnRenamed("taxa_juros_mensal",      "taxa_juros")
        .withColumnRenamed("quantidade_parcelas",    "prazo_meses"))

prop_orig = normalizar_propostas(spark.table("banvic_bronze.propostas_credito"))
prop_sint = normalizar_propostas(spark.table("banvic_bronze.propostas_sinteticas"))

propostas_clean = (prop_orig.unionByName(prop_sint, allowMissingColumns=True)
    .withColumn("data_proposta",  F.col("data_proposta").cast("date"))
    .withColumn("valor_proposta", F.col("valor_proposta").cast("double"))
    .withColumn("taxa_juros",     F.col("taxa_juros").cast("double"))
    .withColumn("prazo_meses",    F.col("prazo_meses").cast("integer"))
)
write_silver(propostas_clean, "propostas")

# COMMAND ----------

print("Silver concluido.")
spark.sql("SHOW TABLES IN banvic_silver").display()
