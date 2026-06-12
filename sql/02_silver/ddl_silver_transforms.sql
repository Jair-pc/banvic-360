-- ================================================================
-- BanVic 360 -- Silver Layer: Transformacoes e Limpeza
-- ================================================================
-- Converte Bronze (TEXT) -> Silver (tipos corretos, padronizados).
-- Executar apos carga_bronze.sql e data_quality_framework.sql
-- ================================================================

-- ── silver.clientes_clean ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.clientes_clean AS
SELECT
    cod_cliente::INTEGER                    AS cod_cliente,
    TRIM(primeiro_nome)                     AS primeiro_nome,
    TRIM(ultimo_nome)                       AS ultimo_nome,
    LOWER(TRIM(email))                      AS email,
    UPPER(TRIM(tipo_cliente))               AS tipo_pessoa,
    data_inclusao::DATE                     AS data_inclusao,
    REGEXP_REPLACE(cpfcnpj, '[^0-9]', '', 'g') AS cpf_digits,
    cpfcnpj                                 AS cpf_formatado,
    data_nascimento::DATE                   AS data_nascimento,
    EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE))::SMALLINT AS idade,
    CASE
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 18 AND 24 THEN '18-24'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 25 AND 34 THEN '25-34'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 35 AND 44 THEN '35-44'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 45 AND 54 THEN '45-54'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 55 AND 64 THEN '55-64'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) >= 65 THEN '65+'
        ELSE 'Menor'
    END                                     AS faixa_etaria,
    TRIM(endereco)                          AS endereco,
    REGEXP_REPLACE(cep, '[^0-9]', '', 'g') AS cep_digits,
    NOW()                                   AS _silver_ts
FROM bronze.clientes
WHERE cod_cliente IS NOT NULL
  AND cpfcnpj IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sc_cod    ON silver.clientes_clean(cod_cliente);
CREATE INDEX IF NOT EXISTS idx_sc_cpf    ON silver.clientes_clean(cpf_digits);
CREATE INDEX IF NOT EXISTS idx_sc_faixa  ON silver.clientes_clean(faixa_etaria);

-- ── silver.clientes_sinteticos_clean ─────────────────────────────

CREATE TABLE IF NOT EXISTS silver.clientes_sinteticos_clean AS
SELECT
    cod_cliente::INTEGER                    AS cod_cliente,
    TRIM(primeiro_nome)                     AS primeiro_nome,
    TRIM(ultimo_nome)                       AS ultimo_nome,
    LOWER(TRIM(email))                      AS email,
    UPPER(tipo_cliente)                     AS tipo_pessoa,
    data_inclusao::DATE                     AS data_inclusao,
    cpfcnpj                                 AS cpf_formatado,
    data_nascimento::DATE                   AS data_nascimento,
    idade::SMALLINT                         AS idade,
    faixa_etaria,
    cidade,
    UPPER(uf)                               AS uf,
    cep,
    renda_mensal::NUMERIC(12,2)             AS renda_mensal,
    faixa_renda,
    profissao,
    escolaridade,
    score_credito::SMALLINT                 AS score_credito,
    faixa_score,
    NOW()                                   AS _silver_ts
FROM bronze.clientes_sinteticos
WHERE cod_cliente IS NOT NULL;

-- ── silver.contas_clean ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.contas_clean AS
SELECT
    num_conta::INTEGER              AS num_conta,
    cod_cliente::INTEGER            AS cod_cliente,
    cod_agencia::INTEGER            AS cod_agencia,
    cod_colaborador::INTEGER        AS cod_colaborador,
    TRIM(tipo_conta)                AS tipo_conta,
    data_abertura::DATE             AS data_abertura,
    -- Limpar floats ruidosos: arredondar para 2 casas
    ROUND(saldo_total::NUMERIC, 2)          AS saldo_total,
    ROUND(saldo_disponivel::NUMERIC, 2)     AS saldo_disponivel,
    data_ultimo_lancamento::DATE            AS data_ultimo_lancamento,
    -- Flag ativa: relativa ao ultimo lancamento do dataset (nao CURRENT_DATE)
    CASE WHEN data_ultimo_lancamento::DATE >=
              (SELECT MAX(data_ultimo_lancamento::DATE) FROM bronze.contas) - 90
         THEN TRUE ELSE FALSE END           AS eh_conta_ativa,
    NOW()                                   AS _silver_ts
FROM bronze.contas
WHERE num_conta IS NOT NULL
  AND saldo_total ~ '^-?[0-9]+\.?[0-9]*$';

CREATE INDEX IF NOT EXISTS idx_cv_num     ON silver.contas_clean(num_conta);
CREATE INDEX IF NOT EXISTS idx_cv_cli     ON silver.contas_clean(cod_cliente);
CREATE INDEX IF NOT EXISTS idx_cv_ag      ON silver.contas_clean(cod_agencia);

-- ── silver.transacoes_clean ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.transacoes_clean AS
SELECT
    cod_transacao::INTEGER          AS cod_transacao,
    num_conta::INTEGER              AS num_conta,
    data_transacao::TIMESTAMP       AS data_transacao,
    DATE_TRUNC('month', data_transacao::TIMESTAMP)::DATE AS mes_referencia,
    TRIM(nome_transacao)            AS nome_transacao,
    valor_transacao::NUMERIC(14,2)  AS valor_transacao,
    ABS(valor_transacao::NUMERIC)   AS valor_absoluto,
    CASE WHEN valor_transacao::NUMERIC >= 0 THEN TRUE ELSE FALSE END AS flag_credito,
    -- Canal derivado do nome da transacao
    CASE
        WHEN nome_transacao ILIKE '%pix%'      THEN 'Pix'
        WHEN nome_transacao ILIKE '%ted%'      THEN 'TED'
        WHEN nome_transacao ILIKE '%doc%'      THEN 'DOC'
        WHEN nome_transacao ILIKE '%credito%'  THEN 'Compra Credito'
        WHEN nome_transacao ILIKE '%debito%'   THEN 'Compra Debito'
        WHEN nome_transacao ILIKE '%saque%'    THEN 'Saque'
        WHEN nome_transacao ILIKE '%deposito%' THEN 'Deposito Especie'
        WHEN nome_transacao ILIKE '%boleto%'   THEN 'Pagamento Boleto'
        ELSE 'Outros'
    END                             AS canal,
    NOW()                           AS _silver_ts
FROM bronze.transacoes
WHERE cod_transacao IS NOT NULL
  AND valor_transacao ~ '^-?[0-9]+\.?[0-9]*$'
  AND valor_transacao::NUMERIC <> 0;

CREATE INDEX IF NOT EXISTS idx_tc_data    ON silver.transacoes_clean(data_transacao);
CREATE INDEX IF NOT EXISTS idx_tc_mes     ON silver.transacoes_clean(mes_referencia);
CREATE INDEX IF NOT EXISTS idx_tc_conta   ON silver.transacoes_clean(num_conta);
CREATE INDEX IF NOT EXISTS idx_tc_canal   ON silver.transacoes_clean(canal);

-- ── silver.agencias_clean ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.agencias_clean AS
SELECT
    a.cod_agencia::INTEGER          AS cod_agencia,
    TRIM(a.nome)                    AS nome,
    UPPER(TRIM(a.tipo_agencia))     AS tipo_agencia,
    a.cidade,
    UPPER(a.uf)                     AS uf,
    CASE UPPER(a.uf)
        WHEN 'SP' THEN 'Sudeste' WHEN 'RJ' THEN 'Sudeste'
        WHEN 'MG' THEN 'Sudeste' WHEN 'ES' THEN 'Sudeste'
        WHEN 'RS' THEN 'Sul'     WHEN 'SC' THEN 'Sul'
        WHEN 'PR' THEN 'Sul'
        WHEN 'BA' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
        WHEN 'CE' THEN 'Nordeste' WHEN 'MA' THEN 'Nordeste'
        WHEN 'PB' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste'
        WHEN 'AL' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste'
        WHEN 'PI' THEN 'Nordeste'
        WHEN 'GO' THEN 'Centro-Oeste' WHEN 'MT' THEN 'Centro-Oeste'
        WHEN 'MS' THEN 'Centro-Oeste' WHEN 'DF' THEN 'Centro-Oeste'
        WHEN 'AM' THEN 'Norte' WHEN 'PA' THEN 'Norte'
        WHEN 'AC' THEN 'Norte' WHEN 'RO' THEN 'Norte'
        WHEN 'RR' THEN 'Norte' WHEN 'AP' THEN 'Norte'
        WHEN 'TO' THEN 'Norte'
        ELSE 'Sudeste'
    END                             AS regiao,
    a.data_abertura::DATE           AS data_abertura,
    COALESCE(e.meta_comercial_mensal::NUMERIC, 500000) AS meta_comercial_mensal,
    COALESCE(e.latitude::NUMERIC, NULL)  AS latitude,
    COALESCE(e.longitude::NUMERIC, NULL) AS longitude,
    TRUE                            AS eh_ativa,
    NOW()                           AS _silver_ts
FROM bronze.agencias a
LEFT JOIN bronze.agencias_expandidas e
       ON e.cod_agencia = a.cod_agencia
WHERE a.cod_agencia IS NOT NULL;

-- ── silver.colaboradores_clean ───────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.colaboradores_clean AS
SELECT
    e.cod_colaborador::INTEGER      AS cod_colaborador,
    e.primeiro_nome,
    e.ultimo_nome,
    LOWER(e.email)                  AS email,
    e.cpf,
    e.data_nascimento::DATE         AS data_nascimento,
    e.cidade,
    UPPER(e.uf)                     AS uf,
    e.regiao,
    e.cargo,
    e.nivel_hierarquico::SMALLINT   AS nivel_hierarquico,
    e.departamento,
    e.salario_base::NUMERIC(12,2)   AS salario_base,
    e.cod_agencia::INTEGER          AS cod_agencia,
    e.data_admissao::DATE           AS data_admissao,
    NULLIF(e.data_demissao, '')::DATE AS data_demissao,
    e.eh_ativo::BOOLEAN             AS eh_ativo,
    NOW()                           AS _silver_ts
FROM bronze.colaboradores_expandidos e
WHERE e.cod_colaborador IS NOT NULL

UNION ALL

-- Colaboradores originais que nao estao no expandido
SELECT
    c.cod_colaborador::INTEGER,
    c.primeiro_nome,
    c.ultimo_nome,
    LOWER(c.email),
    c.cpf,
    c.data_nascimento::DATE,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL::DATE, NULL::DATE,
    TRUE,
    NOW()
FROM bronze.colaboradores c
WHERE NOT EXISTS (
    SELECT 1 FROM bronze.colaboradores_expandidos e
    WHERE e.cod_colaborador = c.cod_colaborador
);

-- ── silver.propostas_clean ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.propostas_clean AS
SELECT
    cod_proposta::INTEGER                   AS cod_proposta,
    cod_cliente::INTEGER                    AS cod_cliente,
    cod_colaborador::INTEGER                AS cod_colaborador,
    data_entrada_proposta::DATE             AS data_entrada_proposta,
    taxa_juros_mensal::NUMERIC(8,6)         AS taxa_juros_mensal,
    valor_proposta::NUMERIC(14,2)           AS valor_proposta,
    valor_financiamento::NUMERIC(14,2)      AS valor_financiamento,
    valor_entrada::NUMERIC(14,2)            AS valor_entrada,
    valor_prestacao::NUMERIC(14,2)          AS valor_prestacao,
    quantidade_parcelas::SMALLINT           AS quantidade_parcelas,
    COALESCE(NULLIF(carencia, '')::SMALLINT, 0) AS carencia_dias,
    TRIM(status_proposta)                   AS status_proposta,
    NOW()                                   AS _silver_ts
FROM bronze.propostas_credito
WHERE cod_proposta IS NOT NULL
  AND valor_proposta ~ '^[0-9]+\.?[0-9]*$'

UNION ALL

SELECT
    cod_proposta::INTEGER,
    cod_cliente::INTEGER,
    cod_colaborador::INTEGER,
    data_entrada_proposta::DATE,
    taxa_juros_mensal::NUMERIC(8,6),
    valor_proposta::NUMERIC(14,2),
    valor_financiamento::NUMERIC(14,2),
    valor_entrada::NUMERIC(14,2),
    valor_prestacao::NUMERIC(14,2),
    quantidade_parcelas::SMALLINT,
    COALESCE(NULLIF(carencia, '')::SMALLINT, 0),
    TRIM(status_proposta),
    NOW()
FROM bronze.propostas_sinteticas
WHERE cod_proposta IS NOT NULL;

-- ── silver.ipca_clean ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.ipca_clean AS
SELECT
    data::DATE                      AS data,
    ano::SMALLINT                   AS ano,
    mes,
    mes_num::SMALLINT               AS mes_num,
    indice::NUMERIC(10,2)           AS indice,
    no_mes::NUMERIC(6,2)            AS variacao_mensal,
    acumulado_12m::NUMERIC(6,2)     AS acumulado_12m,
    acumulado_ano::NUMERIC(6,2)     AS acumulado_ano,
    'REAL'                          AS tipo,
    NOW()                           AS _silver_ts
FROM bronze.ipca
WHERE data ~ '^\d{4}-\d{2}-\d{2}$'

UNION ALL

SELECT
    data::DATE, ano::SMALLINT, mes, mes_num::SMALLINT,
    indice::NUMERIC(10,2), no_mes::NUMERIC(6,2),
    acumulado_12m::NUMERIC(6,2), acumulado_ano::NUMERIC(6,2),
    tipo, NOW()
FROM bronze.ipca_projetado
WHERE tipo = 'PROJECAO';

CREATE UNIQUE INDEX IF NOT EXISTS idx_ipca_data ON silver.ipca_clean(data);

-- ── silver.selic_clean ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.selic_clean AS
SELECT
    data::DATE                      AS data,
    taxa_selic::NUMERIC(10,6)       AS taxa_selic,
    taxa_selic::NUMERIC * 252 * 100 AS taxa_selic_aa,
    'REAL'                          AS tipo,
    NOW()                           AS _silver_ts
FROM bronze.selic

UNION ALL

SELECT
    data::DATE,
    taxa_selic::NUMERIC(10,6),
    taxa_selic::NUMERIC * 252 * 100,
    tipo,
    NOW()
FROM bronze.selic_projetada
WHERE tipo = 'PROJECAO';

CREATE UNIQUE INDEX IF NOT EXISTS idx_selic_data ON silver.selic_clean(data);

-- ── silver.municipios_clean ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS silver.municipios_clean AS
SELECT
    m.codigo_ibge::INTEGER          AS codigo_ibge,
    m.municipio,
    UPPER(m.uf)                     AS uf,
    CASE UPPER(m.uf)
        WHEN 'SP' THEN 'Sudeste' WHEN 'RJ' THEN 'Sudeste'
        WHEN 'MG' THEN 'Sudeste' WHEN 'ES' THEN 'Sudeste'
        WHEN 'RS' THEN 'Sul'     WHEN 'SC' THEN 'Sul'   WHEN 'PR' THEN 'Sul'
        WHEN 'BA' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
        WHEN 'CE' THEN 'Nordeste' WHEN 'MA' THEN 'Nordeste'
        WHEN 'PB' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste'
        WHEN 'AL' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste' WHEN 'PI' THEN 'Nordeste'
        WHEN 'GO' THEN 'Centro-Oeste' WHEN 'MT' THEN 'Centro-Oeste'
        WHEN 'MS' THEN 'Centro-Oeste' WHEN 'DF' THEN 'Centro-Oeste'
        WHEN 'AM' THEN 'Norte' WHEN 'PA' THEN 'Norte'
        WHEN 'AC' THEN 'Norte' WHEN 'RO' THEN 'Norte'
        WHEN 'RR' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'TO' THEN 'Norte'
        ELSE 'Sudeste'
    END                             AS regiao,
    p.populacao::INTEGER            AS populacao,
    p.ano::SMALLINT                 AS ano_populacao,
    pib.pib_total::BIGINT           AS pib_total,
    pib.pib_per_capita::NUMERIC     AS pib_per_capita,
    pib.ano::SMALLINT               AS ano_pib,
    NOW()                           AS _silver_ts
FROM bronze.municipios m
LEFT JOIN bronze.populacao p
       ON p.codigo_ibge = m.codigo_ibge AND p.ano = '2022'
LEFT JOIN bronze.pib_municipal pib
       ON pib.codigo_ibge = m.codigo_ibge AND pib.ano = '2021';

CREATE INDEX IF NOT EXISTS idx_mun_ibge ON silver.municipios_clean(codigo_ibge);
CREATE INDEX IF NOT EXISTS idx_mun_uf   ON silver.municipios_clean(uf);

-- ── Verificacao pos-Silver ────────────────────────────────────────

SELECT 'clientes_clean'        AS tabela, COUNT(*) AS linhas FROM silver.clientes_clean
UNION ALL SELECT 'contas_clean',           COUNT(*) FROM silver.contas_clean
UNION ALL SELECT 'transacoes_clean',       COUNT(*) FROM silver.transacoes_clean
UNION ALL SELECT 'agencias_clean',         COUNT(*) FROM silver.agencias_clean
UNION ALL SELECT 'colaboradores_clean',    COUNT(*) FROM silver.colaboradores_clean
UNION ALL SELECT 'propostas_clean',        COUNT(*) FROM silver.propostas_clean
UNION ALL SELECT 'ipca_clean',             COUNT(*) FROM silver.ipca_clean
UNION ALL SELECT 'selic_clean',            COUNT(*) FROM silver.selic_clean
UNION ALL SELECT 'municipios_clean',       COUNT(*) FROM silver.municipios_clean
ORDER BY tabela;
