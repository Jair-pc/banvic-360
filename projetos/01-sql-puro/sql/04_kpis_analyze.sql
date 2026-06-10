-- ================================================================
-- BanVic 360 -- Projeto 1: SQL Puro
-- 04_kpis_analyze.sql -- 8 KPIs com EXPLAIN ANALYZE
-- ================================================================
-- Para ver o plano de execucao de cada KPI:
--   EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) <query>
-- ================================================================

-- ── KPI 1: Saldo sob gestao por agencia ──────────────────────────
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    a.cod_agencia,
    a.nome                              AS nome_agencia,
    COUNT(DISTINCT fc.num_conta)        AS qtd_contas,
    SUM(fc.saldo_total)                 AS saldo_total,
    AVG(fc.saldo_total)                 AS saldo_medio
FROM gold.fato_contas fc
JOIN gold.dim_agencia a ON a.sk_agencia = fc.sk_agencia
WHERE fc.eh_conta_ativa = TRUE
GROUP BY a.cod_agencia, a.nome
ORDER BY saldo_total DESC;


-- ── KPI 2 + 3: Volume e mix por mes e tipo de transacao ──────────
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    t.ano,
    t.mes,
    t.mes_nome,
    ft.nome_transacao,
    COUNT(*)                            AS qtd_transacoes,
    SUM(ft.valor_absoluto)              AS volume_total,
    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (PARTITION BY t.ano, t.mes),
        2
    )                                   AS pct_mix
FROM gold.fato_transacoes ft
JOIN gold.dim_tempo t ON t.sk_tempo = ft.sk_tempo
GROUP BY t.ano, t.mes, t.mes_nome, ft.nome_transacao
ORDER BY t.ano, t.mes, volume_total DESC;


-- ── KPI 4: Conversao de propostas ────────────────────────────────
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    fp.status_proposta,
    COUNT(*)                            AS qtd_propostas,
    SUM(fp.valor_proposta)              AS valor_total,
    AVG(fp.valor_proposta)              AS valor_medio,
    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (),
        2
    )                                   AS pct_status
FROM gold.fato_propostas_credito fp
GROUP BY fp.status_proposta
ORDER BY qtd_propostas DESC;


-- ── KPI 5: Ranking de agencias (saldo + volume) ───────────────────
EXPLAIN (ANALYZE, BUFFERS)
WITH saldo AS (
    SELECT
        a.cod_agencia,
        a.nome                          AS nome_agencia,
        a.cidade, a.uf,
        COUNT(DISTINCT fc.num_conta)    AS qtd_contas,
        SUM(fc.saldo_total)             AS saldo_total,
        AVG(fc.saldo_total)             AS saldo_medio
    FROM gold.fato_contas fc
    JOIN gold.dim_agencia a ON a.sk_agencia = fc.sk_agencia
    WHERE fc.eh_conta_ativa = TRUE
    GROUP BY a.cod_agencia, a.nome, a.cidade, a.uf
),
volume AS (
    SELECT
        a.cod_agencia,
        SUM(ft.valor_absoluto)          AS volume_total
    FROM gold.fato_transacoes ft
    JOIN gold.dim_agencia a ON a.sk_agencia = ft.sk_agencia
    GROUP BY a.cod_agencia
)
SELECT
    ROW_NUMBER() OVER (ORDER BY s.saldo_total DESC, COALESCE(v.volume_total, 0) DESC) AS ranking,
    s.cod_agencia, s.nome_agencia, s.cidade, s.uf,
    s.qtd_contas, s.saldo_total, s.saldo_medio,
    COALESCE(v.volume_total, 0) AS volume_total
FROM saldo s
LEFT JOIN volume v ON v.cod_agencia = s.cod_agencia
ORDER BY ranking;


-- ── KPI 6: Carteira por colaborador ──────────────────────────────
EXPLAIN (ANALYZE, BUFFERS)
WITH contas_col AS (
    SELECT
        fc.sk_colaborador,
        COUNT(DISTINCT fc.num_conta)    AS qtd_contas,
        SUM(fc.saldo_total)             AS saldo_total
    FROM gold.fato_contas fc
    WHERE fc.eh_conta_ativa = TRUE
    GROUP BY fc.sk_colaborador
),
props_col AS (
    SELECT
        fp.sk_colaborador,
        COUNT(*)                        AS qtd_propostas,
        COUNT(*) FILTER (WHERE fp.status_proposta = 'Aprovada') AS propostas_aprovadas
    FROM gold.fato_propostas_credito fp
    GROUP BY fp.sk_colaborador
)
SELECT
    col.cod_colaborador,
    col.nome_completo,
    col.cargo,
    ag.nome                             AS agencia,
    COALESCE(cc.qtd_contas, 0)          AS qtd_contas_geridas,
    COALESCE(cc.saldo_total, 0)         AS saldo_gerido,
    COALESCE(pc.qtd_propostas, 0)       AS qtd_propostas,
    COALESCE(pc.propostas_aprovadas, 0) AS propostas_aprovadas
FROM gold.dim_colaborador col
JOIN gold.dim_agencia ag ON ag.sk_agencia = col.sk_agencia_principal
LEFT JOIN contas_col cc  ON cc.sk_colaborador = col.sk_colaborador
LEFT JOIN props_col pc   ON pc.sk_colaborador = col.sk_colaborador
WHERE col.eh_ativo = TRUE
ORDER BY saldo_gerido DESC NULLS LAST;


-- ── KPI 7: Segmentacao por faixa etaria ──────────────────────────
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    cli.faixa_etaria,
    COUNT(DISTINCT cli.sk_cliente)      AS qtd_clientes,
    COUNT(DISTINCT fc.num_conta)        AS qtd_contas,
    ROUND(AVG(fc.saldo_total), 2)       AS saldo_medio,
    SUM(fc.saldo_total)                 AS saldo_total
FROM gold.dim_cliente cli
LEFT JOIN gold.fato_contas fc
    ON fc.sk_cliente = cli.sk_cliente
   AND fc.eh_conta_ativa = TRUE
WHERE cli.eh_registro_atual = TRUE
GROUP BY cli.faixa_etaria
ORDER BY cli.faixa_etaria;


-- ── KPI 8: Correcao IPCA ─────────────────────────────────────────
EXPLAIN (ANALYZE, BUFFERS)
WITH base_ipca AS (
    SELECT indice_ipca
    FROM gold.dim_tempo
    WHERE data = (
        SELECT MAX(data) FROM gold.dim_tempo WHERE indice_ipca IS NOT NULL
    )
    LIMIT 1
)
SELECT
    t.ano,
    t.mes,
    t.mes_nome,
    t.indice_ipca                       AS indice_mes,
    b.indice_ipca                       AS indice_base,
    SUM(ft.valor_absoluto)              AS volume_nominal,
    ROUND(
        SUM(ft.valor_absoluto) * b.indice_ipca / NULLIF(t.indice_ipca, 0),
        2
    )                                   AS volume_real
FROM gold.fato_transacoes ft
JOIN gold.dim_tempo t ON t.sk_tempo = ft.sk_tempo
CROSS JOIN base_ipca b
WHERE t.indice_ipca IS NOT NULL
GROUP BY t.ano, t.mes, t.mes_nome, t.indice_ipca, b.indice_ipca
ORDER BY t.ano, t.mes;
