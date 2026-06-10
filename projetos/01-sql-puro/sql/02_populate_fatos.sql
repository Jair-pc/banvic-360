-- ================================================================
-- BanVic 360 -- Projeto 1: SQL Puro
-- 02_populate_fatos.sql -- Carga dos fatos Gold
-- ================================================================
-- Silver -> Gold: popula as tabelas fato com chaves surrogate.
-- Usa lookup das dims para resolver FKs.
-- ================================================================

-- ── fato_transacoes ───────────────────────────────────────────────
TRUNCATE gold.fato_transacoes CASCADE;

INSERT INTO gold.fato_transacoes (
    cod_transacao,
    sk_tempo, sk_cliente, sk_agencia, sk_canal,
    num_conta, nome_transacao,
    valor_transacao, flag_credito
)
SELECT
    tx.cod_transacao,
    t.sk_tempo,
    cli.sk_cliente,
    ag.sk_agencia,
    can.sk_canal,
    tx.num_conta,
    tx.nome_transacao,
    tx.valor_transacao,
    tx.flag_credito
FROM silver.transacoes_clean tx
-- Lookup dim_tempo: usar a data (sem hora) da transacao
JOIN gold.dim_tempo t
    ON t.data = tx.data_transacao::DATE
-- Lookup conta -> cliente -> agencia
JOIN silver.contas_clean c
    ON c.num_conta = tx.num_conta
JOIN gold.dim_cliente cli
    ON cli.cod_cliente = c.cod_cliente
   AND cli.eh_registro_atual = TRUE
JOIN gold.dim_agencia ag
    ON ag.cod_agencia = c.cod_agencia
-- Lookup canal
LEFT JOIN gold.dim_canal can
    ON can.nome_canal = tx.canal;


-- ── fato_contas (snapshot corrente -- 1 linha por conta) ─────────
TRUNCATE gold.fato_contas CASCADE;

INSERT INTO gold.fato_contas (
    sk_tempo, sk_cliente, sk_agencia, sk_colaborador,
    num_conta,
    saldo_total, saldo_disponivel,
    eh_conta_ativa
)
SELECT
    t.sk_tempo,
    cli.sk_cliente,
    ag.sk_agencia,
    col.sk_colaborador,
    c.num_conta,
    c.saldo_total,
    c.saldo_disponivel,
    TRUE AS eh_conta_ativa
FROM silver.contas_clean c
-- Dim tempo: data do ultimo lancamento (ou hoje se nulo)
JOIN gold.dim_tempo t
    ON t.data = COALESCE(c.data_ultimo_lancamento, CURRENT_DATE)
JOIN gold.dim_cliente cli
    ON cli.cod_cliente = c.cod_cliente
   AND cli.eh_registro_atual = TRUE
JOIN gold.dim_agencia ag
    ON ag.cod_agencia = c.cod_agencia
LEFT JOIN gold.dim_colaborador col
    ON col.cod_colaborador = c.cod_colaborador;


-- ── fato_propostas_credito ────────────────────────────────────────
TRUNCATE gold.fato_propostas_credito CASCADE;

INSERT INTO gold.fato_propostas_credito (
    cod_proposta,
    sk_tempo_entrada, sk_cliente, sk_colaborador,
    status_proposta,
    valor_proposta, valor_financiamento, valor_entrada,
    valor_prestacao, quantidade_parcelas,
    taxa_juros_mensal
)
SELECT
    p.cod_proposta::INTEGER,
    t_entrada.sk_tempo,
    cli.sk_cliente,
    col.sk_colaborador,
    p.status_proposta,
    p.valor_proposta::NUMERIC,
    p.valor_financiamento::NUMERIC,
    p.valor_entrada::NUMERIC,
    p.valor_prestacao::NUMERIC,
    p.quantidade_parcelas::SMALLINT,
    p.taxa_juros_mensal::NUMERIC
FROM bronze.propostas_credito p
JOIN gold.dim_tempo t_entrada
    ON t_entrada.data = p.data_entrada_proposta::DATE
JOIN gold.dim_cliente cli
    ON cli.cod_cliente = p.cod_cliente::INTEGER
   AND cli.eh_registro_atual = TRUE
LEFT JOIN gold.dim_colaborador col
    ON col.cod_colaborador = p.cod_colaborador::INTEGER
WHERE p.cod_proposta IS NOT NULL
  AND p.data_entrada_proposta IS NOT NULL;
