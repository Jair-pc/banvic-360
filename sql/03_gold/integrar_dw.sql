-- ============================================================
-- BanVic - Scripts SQL para integração de dados externos ao DW
-- ============================================================
-- Execução: PostgreSQL 14+
-- Ordem de execução:
--   1. Criar tabelas staging
--   2. Criar tabelas dimensão/fato no Gold
--   3. Importar CSVs (via COPY ou ferramenta ETL)
--   4. Executar transformações finais
-- ============================================================


-- ────────────────────────────────────────────────────────────
-- SCHEMA
-- ────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS gold;


-- ════════════════════════════════════════════════════════════
-- 1. TABELAS STAGING (dados brutos dos CSVs)
-- ════════════════════════════════════════════════════════════

-- 1.1 Dólar PTAX
CREATE TABLE IF NOT EXISTS staging.dolar_ptax (
    data             DATE        NOT NULL,
    cotacao_compra   NUMERIC(10,4),
    cotacao_venda    NUMERIC(10,4),
    cotacao_media    NUMERIC(10,4)
);

-- 1.2 Taxa Selic
CREATE TABLE IF NOT EXISTS staging.selic (
    data        DATE        NOT NULL,
    taxa_selic  NUMERIC(8,4)
);

-- 1.3 Feriados Nacionais
CREATE TABLE IF NOT EXISTS staging.feriados (
    data          DATE        NOT NULL,
    nome_feriado  VARCHAR(200) NOT NULL,
    tipo          VARCHAR(50)
);

-- 1.4 Municípios
CREATE TABLE IF NOT EXISTS staging.municipios (
    codigo_ibge   INTEGER     NOT NULL,
    municipio     VARCHAR(150) NOT NULL,
    uf            CHAR(2)     NOT NULL,
    uf_nome       VARCHAR(50),
    regiao        VARCHAR(20),
    regiao_sigla  CHAR(2)
);

-- 1.5 População
CREATE TABLE IF NOT EXISTS staging.populacao (
    codigo_ibge   INTEGER     NOT NULL,
    municipio     VARCHAR(150),
    ano           SMALLINT    NOT NULL,
    populacao     INTEGER     NOT NULL
);

-- 1.6 PIB Municipal
CREATE TABLE IF NOT EXISTS staging.pib_municipal (
    codigo_ibge   INTEGER     NOT NULL,
    municipio     VARCHAR(150),
    ano           SMALLINT    NOT NULL,
    pib_total     BIGINT,
    pib_per_capita NUMERIC(14,2)
);


-- ════════════════════════════════════════════════════════════
-- 2. IMPORTAÇÃO DOS CSVs (ajuste o caminho conforme ambiente)
-- ════════════════════════════════════════════════════════════

-- Execute no psql ou via pgAdmin, ajustando o caminho base:

-- TRUNCATE staging.dolar_ptax;
-- COPY staging.dolar_ptax FROM '/dados/external/dolar_ptax.csv'
--     CSV HEADER DELIMITER ',' ENCODING 'UTF8';

-- TRUNCATE staging.selic;
-- COPY staging.selic FROM '/dados/external/selic.csv'
--     CSV HEADER DELIMITER ',' ENCODING 'UTF8';

-- TRUNCATE staging.feriados;
-- COPY staging.feriados FROM '/dados/external/feriados.csv'
--     CSV HEADER DELIMITER ',' ENCODING 'UTF8';

-- TRUNCATE staging.municipios;
-- COPY staging.municipios FROM '/dados/external/municipios.csv'
--     CSV HEADER DELIMITER ',' ENCODING 'UTF8';

-- TRUNCATE staging.populacao;
-- COPY staging.populacao FROM '/dados/external/populacao.csv'
--     CSV HEADER DELIMITER ',' ENCODING 'UTF8';

-- TRUNCATE staging.pib_municipal;
-- COPY staging.pib_municipal FROM '/dados/external/pib_municipal.csv'
--     CSV HEADER DELIMITER ',' ENCODING 'UTF8';


-- ════════════════════════════════════════════════════════════
-- 3. DIMENSÃO TEMPO (dim_tempo) — integrar feriados e Selic
-- ════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS gold.dim_tempo (
    sk_tempo          SERIAL PRIMARY KEY,
    data              DATE        NOT NULL UNIQUE,
    ano               SMALLINT    NOT NULL,
    trimestre         SMALLINT    NOT NULL,
    mes               SMALLINT    NOT NULL,
    mes_nome          VARCHAR(20) NOT NULL,
    semana_ano        SMALLINT,
    dia_semana        SMALLINT    NOT NULL,  -- 0=Dom, 6=Sab
    dia_semana_nome   VARCHAR(15) NOT NULL,
    eh_fim_semana     BOOLEAN     NOT NULL DEFAULT FALSE,
    eh_feriado        BOOLEAN     NOT NULL DEFAULT FALSE,
    nome_feriado      VARCHAR(200),
    tipo_feriado      VARCHAR(50),
    taxa_selic_dia    NUMERIC(8,4),
    cotacao_dolar     NUMERIC(10,4)
);

-- Populate dim_tempo from 2020-01-01 to 2025-12-31
INSERT INTO gold.dim_tempo (
    data, ano, trimestre, mes, mes_nome, semana_ano,
    dia_semana, dia_semana_nome, eh_fim_semana
)
SELECT
    d::DATE                                        AS data,
    EXTRACT(YEAR  FROM d)::SMALLINT               AS ano,
    EXTRACT(QUARTER FROM d)::SMALLINT             AS trimestre,
    EXTRACT(MONTH FROM d)::SMALLINT               AS mes,
    TO_CHAR(d, 'TMMonth')                         AS mes_nome,
    EXTRACT(WEEK  FROM d)::SMALLINT               AS semana_ano,
    EXTRACT(DOW   FROM d)::SMALLINT               AS dia_semana,
    TO_CHAR(d, 'TMDay')                           AS dia_semana_nome,
    EXTRACT(DOW FROM d) IN (0, 6)                 AS eh_fim_semana
FROM generate_series('2020-01-01'::DATE, '2025-12-31'::DATE, '1 day') AS d
ON CONFLICT (data) DO NOTHING;

-- Enriquecer com feriados
UPDATE gold.dim_tempo t
SET
    eh_feriado   = TRUE,
    nome_feriado = f.nome_feriado,
    tipo_feriado = f.tipo
FROM staging.feriados f
WHERE t.data = f.data;

-- Enriquecer com Selic
UPDATE gold.dim_tempo t
SET taxa_selic_dia = s.taxa_selic
FROM staging.selic s
WHERE t.data = s.data;

-- Enriquecer com PTAX
UPDATE gold.dim_tempo t
SET cotacao_dolar = p.cotacao_media
FROM staging.dolar_ptax p
WHERE t.data = p.data;


-- ════════════════════════════════════════════════════════════
-- 4. DIMENSÃO MUNICÍPIO ENRIQUECIDA (dim_municipio)
-- ════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS gold.dim_municipio (
    sk_municipio    SERIAL PRIMARY KEY,
    codigo_ibge     INTEGER     NOT NULL UNIQUE,
    municipio       VARCHAR(150) NOT NULL,
    uf              CHAR(2)     NOT NULL,
    uf_nome         VARCHAR(50),
    regiao          VARCHAR(20),
    regiao_sigla    CHAR(2),
    populacao       INTEGER,
    ano_populacao   SMALLINT,
    pib_total       BIGINT,
    pib_per_capita  NUMERIC(14,2),
    ano_pib         SMALLINT
);

INSERT INTO gold.dim_municipio (
    codigo_ibge, municipio, uf, uf_nome, regiao, regiao_sigla,
    populacao, ano_populacao, pib_total, pib_per_capita, ano_pib
)
SELECT
    m.codigo_ibge,
    m.municipio,
    m.uf,
    m.uf_nome,
    m.regiao,
    m.regiao_sigla,
    p.populacao,
    p.ano,
    pib.pib_total,
    pib.pib_per_capita,
    pib.ano
FROM staging.municipios m
LEFT JOIN staging.populacao   p   ON p.codigo_ibge = m.codigo_ibge
LEFT JOIN staging.pib_municipal pib ON pib.codigo_ibge = m.codigo_ibge
ON CONFLICT (codigo_ibge) DO UPDATE
SET
    populacao      = EXCLUDED.populacao,
    pib_total      = EXCLUDED.pib_total,
    pib_per_capita = EXCLUDED.pib_per_capita;


-- ════════════════════════════════════════════════════════════
-- 5. INTEGRAÇÃO COM TABELAS INTERNAS DO BANVIC
-- ════════════════════════════════════════════════════════════

-- 5.1 Linkar agências ao município enriquecido
-- (supõe que agencias.csv tem campo 'cidade' e 'uf')
ALTER TABLE gold.dim_agencia
    ADD COLUMN IF NOT EXISTS sk_municipio  INTEGER REFERENCES gold.dim_municipio(sk_municipio);

UPDATE gold.dim_agencia a
SET sk_municipio = dm.sk_municipio
FROM gold.dim_municipio dm
WHERE UPPER(TRIM(a.cidade)) = UPPER(TRIM(dm.municipio))
  AND UPPER(TRIM(a.uf))     = UPPER(TRIM(dm.uf));

-- 5.2 Linkar clientes ao município enriquecido
ALTER TABLE gold.dim_cliente
    ADD COLUMN IF NOT EXISTS sk_municipio  INTEGER REFERENCES gold.dim_municipio(sk_municipio);

UPDATE gold.dim_cliente c
SET sk_municipio = dm.sk_municipio
FROM gold.dim_municipio dm
WHERE UPPER(TRIM(c.cidade)) = UPPER(TRIM(dm.municipio))
  AND UPPER(TRIM(c.uf))     = UPPER(TRIM(dm.uf));


-- ════════════════════════════════════════════════════════════
-- 6. VIEWS ANALÍTICAS DE NEGÓCIO
-- ════════════════════════════════════════════════════════════

-- 6.1 Transações x Câmbio PTAX (valor em USD)
CREATE OR REPLACE VIEW gold.vw_transacoes_em_dolar AS
SELECT
    t.sk_transacao,
    t.data_transacao,
    t.valor_transacao,
    dt.cotacao_dolar,
    CASE
        WHEN dt.cotacao_dolar > 0
        THEN ROUND(t.valor_transacao / dt.cotacao_dolar, 2)
    END AS valor_usd
FROM gold.fato_transacoes t
JOIN gold.dim_tempo dt ON dt.data = t.data_transacao;

-- 6.2 Rentabilidade ajustada pela Selic
CREATE OR REPLACE VIEW gold.vw_rentabilidade_vs_selic AS
SELECT
    t.sk_transacao,
    t.data_transacao,
    t.valor_transacao,
    dt.taxa_selic_dia,
    ROUND(dt.taxa_selic_dia / 252, 6)              AS selic_diaria,
    ROUND(t.valor_transacao * (dt.taxa_selic_dia / 100 / 252), 2) AS custo_oportunidade_dia
FROM gold.fato_transacoes t
JOIN gold.dim_tempo dt ON dt.data = t.data_transacao
WHERE dt.taxa_selic_dia IS NOT NULL;

-- 6.3 Perfil socioeconômico de clientes por município
CREATE OR REPLACE VIEW gold.vw_clientes_por_municipio AS
SELECT
    dm.municipio,
    dm.uf,
    dm.regiao,
    dm.populacao,
    dm.pib_per_capita,
    COUNT(DISTINCT dc.sk_cliente)                  AS qtd_clientes,
    ROUND(COUNT(DISTINCT dc.sk_cliente)::NUMERIC
          / NULLIF(dm.populacao, 0) * 100, 4)      AS penetracao_pct,
    SUM(ft.valor_transacao)                        AS volume_transacoes,
    AVG(ft.valor_transacao)                        AS ticket_medio
FROM gold.dim_municipio dm
LEFT JOIN gold.dim_cliente  dc ON dc.sk_municipio = dm.sk_municipio
LEFT JOIN gold.fato_transacoes ft ON ft.sk_cliente = dc.sk_cliente
GROUP BY dm.sk_municipio, dm.municipio, dm.uf, dm.regiao, dm.populacao, dm.pib_per_capita;

-- 6.4 Dias úteis por mês (exclui fins de semana e feriados)
CREATE OR REPLACE VIEW gold.vw_dias_uteis AS
SELECT
    ano,
    mes,
    mes_nome,
    COUNT(*) FILTER (WHERE NOT eh_fim_semana AND NOT eh_feriado) AS dias_uteis,
    COUNT(*) FILTER (WHERE eh_feriado)                           AS qtd_feriados,
    COUNT(*)                                                     AS total_dias
FROM gold.dim_tempo
GROUP BY ano, mes, mes_nome
ORDER BY ano, mes;

-- 6.5 Análise de crédito por região vs PIB per capita
CREATE OR REPLACE VIEW gold.vw_credito_por_regiao AS
SELECT
    dm.regiao,
    dm.uf,
    AVG(dm.pib_per_capita)                         AS pib_per_capita_medio,
    COUNT(DISTINCT fp.sk_proposta)                 AS qtd_propostas,
    COUNT(DISTINCT fp.sk_proposta) FILTER
        (WHERE fp.status_proposta = 'Aprovada')    AS propostas_aprovadas,
    ROUND(
        COUNT(DISTINCT fp.sk_proposta) FILTER
            (WHERE fp.status_proposta = 'Aprovada')::NUMERIC
        / NULLIF(COUNT(DISTINCT fp.sk_proposta),0) * 100, 2
    )                                              AS taxa_aprovacao_pct,
    AVG(fp.valor_solicitado)                       AS valor_medio_solicitado
FROM gold.dim_municipio dm
JOIN gold.dim_cliente   dc ON dc.sk_municipio = dm.sk_municipio
JOIN gold.fato_propostas fp ON fp.sk_cliente  = dc.sk_cliente
GROUP BY dm.regiao, dm.uf;


-- ════════════════════════════════════════════════════════════
-- 7. ÍNDICES DE PERFORMANCE
-- ════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_dim_tempo_data        ON gold.dim_tempo(data);
CREATE INDEX IF NOT EXISTS idx_dim_tempo_ano_mes      ON gold.dim_tempo(ano, mes);
CREATE INDEX IF NOT EXISTS idx_dim_tempo_eh_feriado   ON gold.dim_tempo(eh_feriado);
CREATE INDEX IF NOT EXISTS idx_dim_municipio_ibge     ON gold.dim_municipio(codigo_ibge);
CREATE INDEX IF NOT EXISTS idx_dim_municipio_uf       ON gold.dim_municipio(uf);
CREATE INDEX IF NOT EXISTS idx_dim_municipio_regiao   ON gold.dim_municipio(regiao);
CREATE INDEX IF NOT EXISTS idx_staging_ptax_data      ON staging.dolar_ptax(data);
CREATE INDEX IF NOT EXISTS idx_staging_selic_data     ON staging.selic(data);
