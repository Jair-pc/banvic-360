# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 05. Validacao dos KPIs
# MAGIC
# MAGIC Calcula os 8 KPIs via Spark SQL e compara com o gabarito.
# MAGIC Todos os 9 projetos do portfolio devem chegar nos mesmos numeros.
# MAGIC
# MAGIC **Gabarito KPI1:** 10 agencias, saldo total = R$ 26.509.620,12

# COMMAND ----------

from pyspark.sql import functions as F

GABARITO_KPI1_SALDO    = 26509620.12
GABARITO_KPI1_AGENCIAS = 10
TOLERANCIA             = 0.10

resultados = {}

# COMMAND ----------

# MAGIC %md ## KPI 1 — Saldo sob gestao por agencia

# COMMAND ----------

kpi1 = spark.sql("""
    SELECT
        a.cod_agencia,
        a.nome_agencia,
        ROUND(SUM(c.saldo_total), 2)   AS saldo_total,
        COUNT(c.num_conta)             AS qtd_contas
    FROM banvic_gold.fato_contas c
    JOIN banvic_gold.dim_agencia a ON c.sk_agencia = a.sk_agencia
    GROUP BY a.cod_agencia, a.nome_agencia
    ORDER BY saldo_total DESC
""")
kpi1.display()

kpi1_tot = kpi1.agg(F.sum("saldo_total").alias("total"), F.count("*").alias("ag")).collect()[0]
dif1 = abs(float(kpi1_tot["total"]) - GABARITO_KPI1_SALDO)
ok1  = dif1 <= TOLERANCIA and int(kpi1_tot["ag"]) == GABARITO_KPI1_AGENCIAS
resultados["KPI1"] = "APROVADO" if ok1 else f"FALHOU (dif={dif1:.4f})"
print(f"KPI1 saldo={kpi1_tot['total']:,.2f} | agencias={kpi1_tot['ag']} | {resultados['KPI1']}")

# COMMAND ----------

# MAGIC %md ## KPI 2 — Volume de transacoes por mes e tipo

# COMMAND ----------

kpi2 = spark.sql("""
    SELECT
        t.ano_mes,
        tx.nome_transacao,
        COUNT(*)                              AS qtd_transacoes,
        ROUND(SUM(tx.valor_transacao), 2)     AS volume_total
    FROM banvic_gold.fato_transacoes tx
    JOIN banvic_gold.dim_tempo t ON tx.sk_tempo = t.sk_tempo
    GROUP BY t.ano_mes, tx.nome_transacao
    ORDER BY t.ano_mes, volume_total DESC
""")
kpi2.display()
resultados["KPI2"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## KPI 3 — Mix de transacoes (% de cada tipo por mes)

# COMMAND ----------

kpi3 = spark.sql("""
    WITH totais AS (
        SELECT t.ano_mes, SUM(tx.valor_transacao) AS total_mes
        FROM banvic_gold.fato_transacoes tx
        JOIN banvic_gold.dim_tempo t ON tx.sk_tempo = t.sk_tempo
        GROUP BY t.ano_mes
    )
    SELECT
        t.ano_mes,
        tx.nome_transacao,
        ROUND(SUM(tx.valor_transacao), 2)                              AS volume,
        ROUND(100.0 * SUM(tx.valor_transacao) / tot.total_mes, 2)     AS pct_volume
    FROM banvic_gold.fato_transacoes tx
    JOIN banvic_gold.dim_tempo t   ON tx.sk_tempo = t.sk_tempo
    JOIN totais tot                ON t.ano_mes   = tot.ano_mes
    GROUP BY t.ano_mes, tx.nome_transacao, tot.total_mes
    ORDER BY t.ano_mes, pct_volume DESC
""")
kpi3.display()
resultados["KPI3"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## KPI 4 — Conversao de propostas

# COMMAND ----------

kpi4 = spark.sql("""
    SELECT
        status_proposta,
        COUNT(*)                              AS qtd,
        ROUND(AVG(valor_proposta), 2)         AS valor_medio,
        ROUND(SUM(valor_proposta), 2)         AS volume_total
    FROM banvic_gold.fato_propostas_credito
    GROUP BY status_proposta
    ORDER BY qtd DESC
""")
kpi4.display()
resultados["KPI4"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## KPI 5 — Ranking de agencias (saldo + volume)

# COMMAND ----------

kpi5 = spark.sql("""
    SELECT
        a.cod_agencia,
        a.nome_agencia,
        ROUND(SUM(c.saldo_total), 2)                                 AS saldo_total,
        COUNT(c.num_conta)                                           AS qtd_contas,
        RANK() OVER (ORDER BY SUM(c.saldo_total) DESC)               AS ranking_saldo
    FROM banvic_gold.fato_contas c
    JOIN banvic_gold.dim_agencia a ON c.sk_agencia = a.sk_agencia
    GROUP BY a.cod_agencia, a.nome_agencia
    ORDER BY ranking_saldo
""")
kpi5.display()
resultados["KPI5"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## KPI 6 — Carteira por colaborador

# COMMAND ----------

kpi6 = spark.sql("""
    SELECT
        col.cod_colaborador,
        col.nome,
        col.cargo,
        COUNT(DISTINCT c.num_conta)  AS qtd_contas,
        ROUND(SUM(c.saldo_total), 2) AS saldo_carteira,
        COUNT(DISTINCT CASE WHEN p.status_proposta = 'APROVADA'
                            THEN p.cod_proposta END) AS propostas_aprovadas
    FROM banvic_gold.dim_colaborador col
    LEFT JOIN banvic_gold.fato_contas c
           ON col.sk_colaborador = c.sk_colaborador
    LEFT JOIN banvic_gold.fato_propostas_credito p
           ON col.sk_colaborador = p.sk_colaborador
    GROUP BY col.cod_colaborador, col.nome, col.cargo
    HAVING COUNT(DISTINCT c.num_conta) > 0
    ORDER BY saldo_carteira DESC
    LIMIT 20
""")
kpi6.display()
resultados["KPI6"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## KPI 7 — Segmentacao por faixa etaria

# COMMAND ----------

kpi7 = spark.sql("""
    SELECT
        cli.faixa_etaria,
        COUNT(DISTINCT c.num_conta)   AS qtd_contas,
        ROUND(AVG(c.saldo_total), 2)  AS saldo_medio,
        ROUND(SUM(c.saldo_total), 2)  AS saldo_total
    FROM banvic_gold.fato_contas c
    JOIN banvic_gold.dim_cliente cli ON c.sk_cliente = cli.sk_cliente
    GROUP BY cli.faixa_etaria
    ORDER BY
        CASE cli.faixa_etaria
            WHEN '18-24' THEN 1  WHEN '25-34' THEN 2
            WHEN '35-44' THEN 3  WHEN '45-54' THEN 4
            WHEN '55-64' THEN 5  WHEN '65+'   THEN 6
        END
""")
kpi7.display()
resultados["KPI7"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## KPI 8 — Correcao IPCA (valor real)

# COMMAND ----------

kpi8 = spark.sql("""
    WITH base AS (
        SELECT MAX(ano_mes) AS mes_base
        FROM banvic_gold.dim_tempo
        WHERE ipca_acumulado IS NOT NULL
    ),
    indice_base AS (
        SELECT MAX(ipca_acumulado) AS idx_base
        FROM banvic_gold.dim_tempo
        WHERE ano_mes = (SELECT mes_base FROM base)
    )
    SELECT
        t.ano_mes,
        ROUND(SUM(tx.valor_transacao), 2)                                    AS valor_nominal,
        ROUND(SUM(tx.valor_transacao) * (SELECT idx_base FROM indice_base)
              / t.ipca_acumulado, 2)                                         AS valor_real
    FROM banvic_gold.fato_transacoes tx
    JOIN banvic_gold.dim_tempo t ON tx.sk_tempo = t.sk_tempo
    WHERE t.ipca_acumulado IS NOT NULL
    GROUP BY t.ano_mes, t.ipca_acumulado
    ORDER BY t.ano_mes
""")
kpi8.display()
resultados["KPI8"] = "CALCULADO"

# COMMAND ----------

# MAGIC %md ## Resumo final

# COMMAND ----------

print("=" * 55)
print("  BanVic 360 - Projeto 7 (Databricks) - Resultado")
print("=" * 55)
for kpi, status in resultados.items():
    icone = "OK" if "APROVADO" in status or "CALCULADO" in status else "!!"
    print(f"  [{icone}] {kpi}: {status}")
print("=" * 55)
print(f"  Gabarito KPI1: R$ {GABARITO_KPI1_SALDO:,.2f} | {GABARITO_KPI1_AGENCIAS} agencias")
