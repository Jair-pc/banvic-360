-- ================================================================
-- BanVic 360 -- Projeto 1: SQL Puro
-- 03_indices.sql -- Indices estrategicos
-- ================================================================
-- Indices escolhidos com base nos padroes de acesso dos 8 KPIs.
-- Cada bloco explica o motivo do indice.
-- ================================================================

-- ── fato_transacoes ───────────────────────────────────────────────

-- KPIs 2, 3: filtro e agrupamento por tempo (ano/mes)
CREATE INDEX IF NOT EXISTS idx_ft_tempo
    ON gold.fato_transacoes(sk_tempo);

-- KPIs 1, 5: join com agencia
CREATE INDEX IF NOT EXISTS idx_ft_agencia
    ON gold.fato_transacoes(sk_agencia);

-- KPI 2: agrupamento por tipo de transacao
CREATE INDEX IF NOT EXISTS idx_ft_nome_tx
    ON gold.fato_transacoes(nome_transacao);

-- KPI 6: join por colaborador via conta -> uso em subqueries
CREATE INDEX IF NOT EXISTS idx_ft_cliente
    ON gold.fato_transacoes(sk_cliente);

-- Indice composto: KPIs 2/3 acessam (sk_tempo, nome_transacao, valor_absoluto)
-- Cobertura permite index-only scan evitando heap
CREATE INDEX IF NOT EXISTS idx_ft_tempo_tx_val
    ON gold.fato_transacoes(sk_tempo, nome_transacao)
    INCLUDE (valor_absoluto);


-- ── fato_contas ───────────────────────────────────────────────────

-- KPI 1, 5: saldo por agencia (acesso frequente)
CREATE INDEX IF NOT EXISTS idx_fc_agencia
    ON gold.fato_contas(sk_agencia)
    INCLUDE (saldo_total, eh_conta_ativa);

-- KPI 6: saldo por colaborador
CREATE INDEX IF NOT EXISTS idx_fc_colaborador
    ON gold.fato_contas(sk_colaborador)
    INCLUDE (saldo_total, num_conta);

-- KPI 7: join com dim_cliente
CREATE INDEX IF NOT EXISTS idx_fc_cliente
    ON gold.fato_contas(sk_cliente)
    INCLUDE (saldo_total);

-- Filtro de contas ativas (usado em todos os KPIs de saldo)
CREATE INDEX IF NOT EXISTS idx_fc_ativa
    ON gold.fato_contas(eh_conta_ativa)
    WHERE eh_conta_ativa = TRUE;


-- ── fato_propostas_credito ────────────────────────────────────────

-- KPI 4: agrupamento por status
CREATE INDEX IF NOT EXISTS idx_fp_status
    ON gold.fato_propostas_credito(status_proposta)
    INCLUDE (valor_proposta);

-- KPI 6: propostas por colaborador
CREATE INDEX IF NOT EXISTS idx_fp_colaborador
    ON gold.fato_propostas_credito(sk_colaborador, status_proposta);


-- ── dim_tempo ─────────────────────────────────────────────────────

-- Lookup por data (usado em todos os JOINs de fato)
CREATE INDEX IF NOT EXISTS idx_dt_data
    ON gold.dim_tempo(data);

-- Filtro por ano/mes (KPIs 2, 3, 4)
CREATE INDEX IF NOT EXISTS idx_dt_ano_mes
    ON gold.dim_tempo(ano, mes)
    INCLUDE (sk_tempo, mes_nome);

-- Filtro por IPCA (KPI 8)
CREATE INDEX IF NOT EXISTS idx_dt_ipca
    ON gold.dim_tempo(indice_ipca)
    WHERE indice_ipca IS NOT NULL;


-- ── dim_cliente ───────────────────────────────────────────────────

-- Lookup por cod_cliente (JOIN de fatos)
CREATE INDEX IF NOT EXISTS idx_dc_cod
    ON gold.dim_cliente(cod_cliente)
    WHERE eh_registro_atual = TRUE;

-- KPI 7: agrupamento por faixa etaria
CREATE INDEX IF NOT EXISTS idx_dc_faixa
    ON gold.dim_cliente(faixa_etaria)
    WHERE eh_registro_atual = TRUE;


-- ── dim_agencia ───────────────────────────────────────────────────

-- Lookup por cod_agencia (JOIN de fatos)
CREATE INDEX IF NOT EXISTS idx_da_cod
    ON gold.dim_agencia(cod_agencia);


-- ── dim_colaborador ───────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_dcol_cod
    ON gold.dim_colaborador(cod_colaborador);

CREATE INDEX IF NOT EXISTS idx_dcol_agencia
    ON gold.dim_colaborador(sk_agencia_principal);
