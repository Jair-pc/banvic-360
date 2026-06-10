-- ================================================================
-- BanVic 360 -- Projeto 1: SQL Puro
-- 01_populate_dims.sql -- Carga das dimensoes Gold
-- ================================================================
-- Silver -> Gold: popula todas as dimensoes a partir dos dados limpos.
-- Idempotente: usa TRUNCATE + INSERT (seguro para re-execucao).
-- ================================================================

-- ── 1. dim_tempo: enriquecer com macroeconomia e feriados ─────────
-- A estrutura de datas ja foi criada pelo DDL.
-- Aqui adicionamos Selic, CDI, PTAX e IPCA por dia.

UPDATE gold.dim_tempo t
SET taxa_selic = s.taxa_selic::NUMERIC
FROM bronze.selic s
WHERE t.data = s.data::DATE
  AND s.taxa_selic ~ '^-?[0-9]+\.?[0-9]*$';

UPDATE gold.dim_tempo t
SET taxa_cdi = c.taxa_cdi::NUMERIC
FROM bronze.cdi c
WHERE t.data = c.data::DATE
  AND c.taxa_cdi ~ '^-?[0-9]+\.?[0-9]*$';

UPDATE gold.dim_tempo t
SET cotacao_dolar = p.cotacao_media::NUMERIC
FROM bronze.dolar_ptax p
WHERE t.data = p.data::DATE
  AND p.cotacao_media ~ '^-?[0-9]+\.?[0-9]*$';

UPDATE gold.dim_tempo t
SET cotacao_euro = e.cotacao_media::NUMERIC
FROM bronze.euro_ptax e
WHERE t.data = e.data::DATE
  AND e.cotacao_media ~ '^-?[0-9]+\.?[0-9]*$';

-- IPCA: todos os dias do mes recebem o mesmo valor mensal
UPDATE gold.dim_tempo t
SET ipca_mes        = i.no_mes::NUMERIC,
    ipca_acum_12m   = i.acumulado_12m::NUMERIC,
    indice_ipca     = i.indice::NUMERIC
FROM bronze.ipca i
WHERE t.ano  = i.ano::SMALLINT
  AND t.mes  = i.mes_num::SMALLINT
  AND i.indice ~ '^-?[0-9]+\.?[0-9]*$';

-- Feriados
UPDATE gold.dim_tempo t
SET eh_feriado   = TRUE,
    nome_feriado = f.nome,
    tipo_feriado = f.tipo,
    eh_dia_util  = FALSE
FROM bronze.feriados f
WHERE t.data = f.data::DATE;


-- ── 2. dim_municipio ─────────────────────────────────────────────
TRUNCATE gold.dim_municipio CASCADE;

INSERT INTO gold.dim_municipio (
    codigo_ibge, municipio, uf,
    populacao, ano_populacao,
    pib_total, pib_per_capita, ano_pib
)
SELECT
    m.codigo_ibge::INTEGER,
    m.municipio,
    m.uf,
    MAX(p.populacao::INTEGER)               AS populacao,
    MAX(p.ano::SMALLINT)                    AS ano_populacao,
    MAX(pib.pib_total::BIGINT)              AS pib_total,
    MAX(pib.pib_per_capita::NUMERIC(14,2))  AS pib_per_capita,
    MAX(pib.ano::SMALLINT)                  AS ano_pib
FROM bronze.municipios m
LEFT JOIN bronze.populacao p
    ON p.codigo_ibge = m.codigo_ibge
   AND p.ano = (SELECT MAX(ano) FROM bronze.populacao WHERE codigo_ibge = m.codigo_ibge)
LEFT JOIN bronze.pib_municipal pib
    ON pib.codigo_ibge = m.codigo_ibge
   AND pib.ano = (SELECT MAX(ano) FROM bronze.pib_municipal WHERE codigo_ibge = m.codigo_ibge)
WHERE m.codigo_ibge IS NOT NULL
GROUP BY m.codigo_ibge, m.municipio, m.uf;


-- ── 3. dim_agencia ───────────────────────────────────────────────
TRUNCATE gold.dim_agencia CASCADE;

INSERT INTO gold.dim_agencia (
    cod_agencia, nome, tipo_agencia,
    cidade, uf, regiao,
    data_abertura, eh_ativa,
    meta_comercial_mensal, latitude, longitude
)
SELECT
    cod_agencia, nome, tipo_agencia,
    cidade, uf, regiao,
    data_abertura, eh_ativa,
    meta_comercial_mensal, latitude, longitude
FROM silver.agencias_clean;


-- ── 4. dim_colaborador ───────────────────────────────────────────
TRUNCATE gold.dim_colaborador CASCADE;

INSERT INTO gold.dim_colaborador (
    cod_colaborador, primeiro_nome, ultimo_nome,
    cpf, email, data_nascimento,
    cargo, departamento, nivel_hierarquico,
    salario_base, data_admissao, data_demissao,
    eh_ativo, sk_agencia_principal, cidade, uf
)
SELECT
    c.cod_colaborador,
    c.primeiro_nome,
    c.ultimo_nome,
    c.cpf,
    c.email,
    c.data_nascimento,
    c.cargo,
    c.departamento,
    c.nivel_hierarquico,
    c.salario_base,
    c.data_admissao,
    c.data_demissao,
    c.eh_ativo,
    a.sk_agencia,
    c.cidade,
    c.uf
FROM silver.colaboradores_clean c
LEFT JOIN gold.dim_agencia a ON a.cod_agencia = c.cod_agencia;


-- ── 5. dim_cliente (simplificado -- sem SCD2 completo) ───────────
TRUNCATE gold.dim_cliente CASCADE;

-- Clientes originais (dados reais)
INSERT INTO gold.dim_cliente (
    cod_cliente, primeiro_nome, ultimo_nome,
    cpf, tipo_pessoa, email,
    data_nascimento, idade, faixa_etaria,
    cep, data_inclusao,
    data_inicio_vigencia, data_fim_vigencia, eh_registro_atual
)
SELECT
    cod_cliente,
    primeiro_nome,
    ultimo_nome,
    cpf_formatado,
    tipo_pessoa,
    email,
    data_nascimento,
    idade,
    faixa_etaria,
    cep_digits,
    data_inclusao,
    data_inclusao,
    '9999-12-31'::DATE,
    TRUE
FROM silver.clientes_clean;

-- Clientes sinteticos (expandidos)
INSERT INTO gold.dim_cliente (
    cod_cliente, primeiro_nome, ultimo_nome,
    tipo_pessoa, email,
    data_nascimento, idade, faixa_etaria,
    cidade, uf,
    renda_mensal, faixa_renda,
    profissao, escolaridade,
    score_credito, faixa_score,
    data_inclusao,
    data_inicio_vigencia, data_fim_vigencia, eh_registro_atual
)
SELECT
    cod_cliente,
    primeiro_nome,
    ultimo_nome,
    tipo_pessoa,
    email,
    data_nascimento,
    idade,
    faixa_etaria,
    cidade,
    uf,
    renda_mensal,
    faixa_renda,
    profissao,
    escolaridade,
    score_credito,
    faixa_score,
    data_inclusao,
    data_inclusao,
    '9999-12-31'::DATE,
    TRUE
FROM silver.clientes_sinteticos_clean;


-- Deduplicar: se cod_cliente existe em ambas as fontes, manter apenas o
-- registro mais recente (sk_cliente maior = inserido por ultimo)
DELETE FROM gold.dim_cliente
WHERE sk_cliente IN (
    SELECT sk_cliente
    FROM (
        SELECT sk_cliente,
               ROW_NUMBER() OVER (PARTITION BY cod_cliente ORDER BY sk_cliente DESC) AS rn
        FROM gold.dim_cliente
        WHERE eh_registro_atual = TRUE
    ) ranked
    WHERE rn > 1
);


-- ── 6. dim_canal (derivado das transacoes) ───────────────────────
TRUNCATE gold.dim_canal CASCADE;

INSERT INTO gold.dim_canal (nome_canal, tipo_canal)
SELECT DISTINCT
    canal AS nome_canal,
    CASE
        WHEN canal IN ('Pix', 'TED', 'DOC')           THEN 'Transferencia'
        WHEN canal IN ('Compra Credito','Compra Debito') THEN 'Cartao'
        WHEN canal IN ('Saque','Deposito Especie')     THEN 'Caixa'
        WHEN canal = 'Pagamento Boleto'                THEN 'Boleto'
        ELSE 'Digital'
    END AS tipo_canal
FROM silver.transacoes_clean
ORDER BY nome_canal;
