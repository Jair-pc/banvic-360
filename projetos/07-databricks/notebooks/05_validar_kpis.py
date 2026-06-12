# Databricks notebook source
# MAGIC %md
# MAGIC # BanVic 360 — 05. Validacao dos KPIs
# MAGIC
# MAGIC Calcula os 8 KPIs via Spark SQL e compara com o gabarito.
# MAGIC Todos os 9 projetos do portfolio devem chegar nos mesmos numeros.
# MAGIC
# MAGIC **Gabarito gerado em 2026-06-10 — imutavel para todos os 9 projetos.**
# MAGIC
# MAGIC | KPI | Gabarito |
# MAGIC |-----|----------|
# MAGIC | 1   | 10 agencias, saldo total = R$ 26.509.620,12 |
# MAGIC | 2/3 | volume total = R$ 58.122.708,67 |
# MAGIC | 4   | 4 status, total = 1.996 propostas |
# MAGIC | 5   | top agencia = 7 |
# MAGIC | 6   | 100 colaboradores, saldo gerido = R$ 26.509.620,12 |
# MAGIC | 7   | 6 faixas etarias, total 50.997 clientes |
# MAGIC | 8   | 155 meses, volume nominal = R$ 58.122.708,67 |

# COMMAND ----------

from pyspark.sql import functions as F

# Gabarito (gerado em 2026-06-10 — imutavel)
GAB_KPI1_AGENCIAS = 10
GAB_KPI1_SALDO    = 26509620.12
GAB_KPI23_VOLUME  = 58122708.67
GAB_KPI4_COUNTS   = [468, 490, 513, 525]   # sorted asc: Em analise, Reprovada, Aprovada, Enviada
GAB_KPI4_TOTAL    = 1996
GAB_KPI5_TOP_AG   = "7"
GAB_KPI6_COLAB    = 100
GAB_KPI6_SALDO    = 26509620.12
GAB_KPI7 = {"18-24": 5312, "25-34": 12021, "35-44": 16346,
             "45-54": 11647, "55-64": 4492, "65+": 1179}
GAB_KPI8_VOLUME   = 58122708.67
GAB_KPI8_MESES    = 155
TOL = 0.10

resultados = {}

# COMMAND ----------

# MAGIC %md ## KPI 1 — Saldo sob gestao por agencia
# MAGIC
# MAGIC Filtro: apenas contas do dataset original (10 agencias do gabarito).

# COMMAND ----------

kpi1 = spark.sql("""
    SELECT
        a.cod_agencia,
        a.nome                       AS nome_agencia,
        ROUND(SUM(c.saldo_total), 2) AS saldo_total,
        COUNT(c.num_conta)           AS qtd_contas
    FROM banvic_gold.fato_contas c
    JOIN banvic_gold.dim_agencia a ON c.sk_agencia = a.sk_agencia
    WHERE c.num_conta IN (SELECT num_conta FROM banvic_bronze.contas)
    GROUP BY a.cod_agencia, a.nome
    ORDER BY saldo_total DESC
""")
kpi1.display()

r1   = kpi1.agg(F.sum("saldo_total").alias("total"), F.count("*").alias("ag")).collect()[0]
dif1 = abs(float(r1["total"]) - GAB_KPI1_SALDO)
ok1  = dif1 <= TOL and int(r1["ag"]) == GAB_KPI1_AGENCIAS
resultados["KPI1"] = "APROVADO" if ok1 else f"FALHOU (saldo={r1['total']:,.2f}, dif={dif1:.4f}, ag={r1['ag']})"
print(f"KPI1   | saldo={r1['total']:,.2f} | ag={r1['ag']} | {resultados['KPI1']}")

# COMMAND ----------

# MAGIC %md ## KPI 2/3 — Volume e mix de transacoes por mes e tipo
# MAGIC
# MAGIC Usa ABS(valor_transacao) — volume bruto independente de sinal.
# MAGIC Filtro: transacoes de contas originais.

# COMMAND ----------

kpi23 = spark.sql("""
    SELECT
        t.ano_mes,
        tx.nome_transacao,
        COUNT(*)                                                                    AS qtd_transacoes,
        ROUND(SUM(ABS(tx.valor_transacao)), 2)                                     AS volume,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY t.ano_mes), 2)  AS pct_mix
    FROM banvic_gold.fato_transacoes tx
    JOIN banvic_gold.dim_tempo t ON tx.sk_tempo = t.sk_tempo
    WHERE tx.num_conta IN (SELECT num_conta FROM banvic_bronze.contas)
    GROUP BY t.ano_mes, tx.nome_transacao
    ORDER BY t.ano_mes, volume DESC
""")
kpi23.display()

r23   = kpi23.agg(F.round(F.sum("volume"), 2).alias("total")).collect()[0]
dif23 = abs(float(r23["total"]) - GAB_KPI23_VOLUME)
ok23  = dif23 <= TOL
resultados["KPI2_3"] = "APROVADO" if ok23 else f"FALHOU (vol={r23['total']:,.2f}, dif={dif23:.4f})"
print(f"KPI2_3 | volume={r23['total']:,.2f} | {resultados['KPI2_3']}")

# COMMAND ----------

# MAGIC %md ## KPI 4 — Conversao de propostas
# MAGIC
# MAGIC fato_propostas_credito contem apenas as propostas originais (1.996 linhas).
# MAGIC Validacao por contagem sorted — evita comparacao de strings com acentos.

# COMMAND ----------

kpi4 = spark.sql("""
    SELECT
        status_proposta,
        COUNT(*)                       AS qtd,
        ROUND(AVG(valor_proposta), 2)  AS valor_medio,
        ROUND(SUM(valor_proposta), 2)  AS volume_total
    FROM banvic_gold.fato_propostas_credito
    GROUP BY status_proposta
    ORDER BY qtd DESC
""")
kpi4.display()

counts4 = sorted([int(r["qtd"]) for r in kpi4.collect()])
total4  = sum(counts4)
ok4     = counts4 == GAB_KPI4_COUNTS and total4 == GAB_KPI4_TOTAL
resultados["KPI4"] = "APROVADO" if ok4 else f"FALHOU (counts={counts4}, total={total4})"
print(f"KPI4   | counts={counts4} | total={total4} | {resultados['KPI4']}")

# COMMAND ----------

# MAGIC %md ## KPI 5 — Ranking de agencias (saldo + volume)

# COMMAND ----------

kpi5 = spark.sql("""
    WITH saldo_ag AS (
        SELECT a.cod_agencia, a.nome AS nome_agencia,
               ROUND(SUM(c.saldo_total), 2) AS saldo_total,
               COUNT(c.num_conta)           AS qtd_contas
        FROM banvic_gold.fato_contas c
        JOIN banvic_gold.dim_agencia a ON c.sk_agencia = a.sk_agencia
        WHERE c.num_conta IN (SELECT num_conta FROM banvic_bronze.contas)
        GROUP BY a.cod_agencia, a.nome
    ),
    volume_ag AS (
        SELECT a.cod_agencia,
               ROUND(SUM(ABS(tx.valor_transacao)), 2) AS volume_total
        FROM banvic_gold.fato_transacoes tx
        JOIN banvic_gold.dim_agencia a ON tx.sk_agencia = a.sk_agencia
        WHERE tx.num_conta IN (SELECT num_conta FROM banvic_bronze.contas)
        GROUP BY a.cod_agencia
    )
    SELECT
        RANK() OVER (ORDER BY s.saldo_total DESC) AS ranking,
        s.cod_agencia, s.nome_agencia,
        s.saldo_total, s.qtd_contas,
        COALESCE(v.volume_total, 0) AS volume_total
    FROM saldo_ag s
    LEFT JOIN volume_ag v ON v.cod_agencia = s.cod_agencia
    ORDER BY ranking
""")
kpi5.display()

rows5 = kpi5.collect()
top5  = str(rows5[0]["cod_agencia"]) if rows5 else ""
ok5   = len(rows5) == GAB_KPI1_AGENCIAS and top5 == GAB_KPI5_TOP_AG
resultados["KPI5"] = "APROVADO" if ok5 else f"FALHOU (ag={len(rows5)}, top={top5})"
print(f"KPI5   | agencias={len(rows5)} | top={top5} | {resultados['KPI5']}")

# COMMAND ----------

# MAGIC %md ## KPI 6 — Carteira por colaborador
# MAGIC
# MAGIC Limita a 100 colaboradores originais (join com banvic_bronze.colaboradores).
# MAGIC Inclui colaboradores com 0 contas (sem HAVING).

# COMMAND ----------

kpi6 = spark.sql("""
    SELECT
        col.cod_colaborador,
        col.nome,
        col.cargo,
        COUNT(DISTINCT c.num_conta)                                       AS qtd_contas,
        ROUND(COALESCE(SUM(c.saldo_total), 0), 2)                        AS saldo_carteira,
        SUM(CASE WHEN p.status_proposta = 'Aprovada' THEN 1 ELSE 0 END)  AS propostas_aprovadas
    FROM banvic_gold.dim_colaborador col
    JOIN banvic_bronze.colaboradores orig
         ON CAST(orig.cod_colaborador AS STRING) = CAST(col.cod_colaborador AS STRING)
    LEFT JOIN banvic_gold.fato_contas c
           ON col.sk_colaborador = c.sk_colaborador
          AND c.num_conta IN (SELECT num_conta FROM banvic_bronze.contas)
    LEFT JOIN banvic_gold.fato_propostas_credito p
           ON col.sk_colaborador = p.sk_colaborador
    GROUP BY col.cod_colaborador, col.nome, col.cargo
    ORDER BY saldo_carteira DESC
""")
kpi6.display()

r6   = kpi6.agg(F.count("*").alias("colab"), F.sum("saldo_carteira").alias("saldo")).collect()[0]
dif6 = abs(float(r6["saldo"]) - GAB_KPI6_SALDO)
ok6  = int(r6["colab"]) == GAB_KPI6_COLAB and dif6 <= TOL
resultados["KPI6"] = "APROVADO" if ok6 else f"FALHOU (colab={r6['colab']}, saldo={r6['saldo']:,.2f}, dif={dif6:.4f})"
print(f"KPI6   | colab={r6['colab']} | saldo={r6['saldo']:,.2f} | {resultados['KPI6']}")

# COMMAND ----------

# MAGIC %md ## KPI 7 — Segmentacao por faixa etaria
# MAGIC
# MAGIC Driver: dim_cliente (todos os 50.997 clientes, original + sintetico).
# MAGIC faixa_etaria foi calculada com data fixa 2026-06-10 no notebook 02_silver.

# COMMAND ----------

kpi7 = spark.sql("""
    SELECT
        cli.faixa_etaria,
        COUNT(DISTINCT cli.sk_cliente)  AS qtd_clientes,
        ROUND(AVG(c.saldo_total), 2)    AS saldo_medio,
        ROUND(SUM(c.saldo_total), 2)    AS saldo_total
    FROM banvic_gold.dim_cliente cli
    LEFT JOIN banvic_gold.fato_contas c ON c.sk_cliente = cli.sk_cliente
    WHERE cli.eh_registro_atual = TRUE
    GROUP BY cli.faixa_etaria
    ORDER BY
        CASE cli.faixa_etaria
            WHEN '18-24' THEN 1  WHEN '25-34' THEN 2
            WHEN '35-44' THEN 3  WHEN '45-54' THEN 4
            WHEN '55-64' THEN 5  WHEN '65+'   THEN 6
        END
""")
kpi7.display()

rows7  = {r["faixa_etaria"]: int(r["qtd_clientes"]) for r in kpi7.collect()}
erros7 = [f"{fx}: {rows7.get(fx,0)} != {qt}" for fx, qt in GAB_KPI7.items() if rows7.get(fx, 0) != qt]
ok7    = len(erros7) == 0
resultados["KPI7"] = "APROVADO" if ok7 else f"FALHOU ({'; '.join(erros7)})"
print(f"KPI7   | {resultados['KPI7']}")

# COMMAND ----------

# MAGIC %md ## KPI 8 — Correcao IPCA (valor real)
# MAGIC
# MAGIC Volume nominal = SUM(ABS(valor_transacao)) por mes.
# MAGIC Valor real = valor nominal * indice_base / indice_mes.

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
        t.ipca_acumulado                                                               AS indice_mes,
        (SELECT idx_base FROM indice_base)                                             AS indice_base,
        ROUND(SUM(ABS(tx.valor_transacao)), 2)                                        AS volume_nominal,
        ROUND(SUM(ABS(tx.valor_transacao)) * (SELECT idx_base FROM indice_base)
              / t.ipca_acumulado, 2)                                                  AS volume_real
    FROM banvic_gold.fato_transacoes tx
    JOIN banvic_gold.dim_tempo t ON tx.sk_tempo = t.sk_tempo
    WHERE t.ipca_acumulado IS NOT NULL
      AND tx.num_conta IN (SELECT num_conta FROM banvic_bronze.contas)
    GROUP BY t.ano_mes, t.ipca_acumulado
    ORDER BY t.ano_mes
""")
kpi8.display()

r8   = kpi8.agg(F.count("*").alias("meses"), F.round(F.sum("volume_nominal"), 2).alias("vol")).collect()[0]
dif8 = abs(float(r8["vol"]) - GAB_KPI8_VOLUME)
ok8  = int(r8["meses"]) == GAB_KPI8_MESES and dif8 <= TOL
resultados["KPI8"] = "APROVADO" if ok8 else f"FALHOU (meses={r8['meses']}, vol={r8['vol']:,.2f}, dif={dif8:.4f})"
print(f"KPI8   | meses={r8['meses']} | volume={r8['vol']:,.2f} | {resultados['KPI8']}")

# COMMAND ----------

# MAGIC %md ## Resumo final

# COMMAND ----------

aprovados = sum(1 for v in resultados.values() if v == "APROVADO")
total     = len(resultados)

print("=" * 55)
print("  BanVic 360 - Projeto 7 (Databricks) - Resultado")
print("=" * 55)
for kpi, status in resultados.items():
    icone = "OK" if status == "APROVADO" else "!!"
    print(f"  [{icone}] {kpi}: {status}")
print("=" * 55)
print(f"  {aprovados}/{total} KPIs APROVADOS")
print("=" * 55)
if aprovados < total:
    raise Exception(f"Validacao falhou: {aprovados}/{total} KPIs aprovados")
