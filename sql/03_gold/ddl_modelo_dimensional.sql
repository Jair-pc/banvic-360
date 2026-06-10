-- ================================================================
-- BanVic 360° — DDL Completo do Modelo Dimensional (Gold Layer)
-- ================================================================
-- PostgreSQL 14+
-- Executar na ordem: schemas → dimensões → fatos → índices → views
-- ================================================================

-- ── SCHEMAS ───────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ================================================================
-- DIMENSÕES
-- ================================================================

-- ── dim_tempo ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_tempo (
    sk_tempo            SERIAL          PRIMARY KEY,
    data                DATE            NOT NULL UNIQUE,
    ano                 SMALLINT        NOT NULL,
    semestre            SMALLINT        NOT NULL,
    trimestre           SMALLINT        NOT NULL,
    mes                 SMALLINT        NOT NULL,
    mes_nome            VARCHAR(20)     NOT NULL,
    mes_abrev           CHAR(3)         NOT NULL,
    semana_ano          SMALLINT        NOT NULL,
    dia_mes             SMALLINT        NOT NULL,
    dia_semana          SMALLINT        NOT NULL,  -- 0=Dom, 6=Sab
    dia_semana_nome     VARCHAR(15)     NOT NULL,
    dia_semana_abrev    CHAR(3)         NOT NULL,
    eh_fim_semana       BOOLEAN         NOT NULL DEFAULT FALSE,
    eh_feriado          BOOLEAN         NOT NULL DEFAULT FALSE,
    nome_feriado        VARCHAR(200),
    tipo_feriado        VARCHAR(50),
    eh_dia_util         BOOLEAN         NOT NULL DEFAULT TRUE,  -- !feriado && !fim_semana
    -- Indicadores macroeconômicos do dia
    taxa_selic          NUMERIC(8,4),   -- % a.a.
    taxa_cdi            NUMERIC(8,4),   -- % a.a.
    cotacao_dolar       NUMERIC(10,4),  -- R$/USD PTAX fechamento
    cotacao_euro        NUMERIC(10,4),  -- R$/EUR PTAX fechamento
    -- IPCA do mês (todos os dias do mês recebem o mesmo valor)
    ipca_mes            NUMERIC(6,2),   -- % no mês
    ipca_acum_12m       NUMERIC(6,2),   -- % acumulado 12 meses
    indice_ipca         NUMERIC(10,2),  -- número-índice acumulado
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- Popular dim_tempo 2020-01-01 até 2026-12-31
INSERT INTO gold.dim_tempo (
    data, ano, semestre, trimestre, mes, mes_nome, mes_abrev,
    semana_ano, dia_mes, dia_semana, dia_semana_nome, dia_semana_abrev,
    eh_fim_semana, eh_dia_util
)
SELECT
    d::DATE,
    EXTRACT(YEAR FROM d)::SMALLINT,
    CASE WHEN EXTRACT(MONTH FROM d) <= 6 THEN 1 ELSE 2 END::SMALLINT,
    EXTRACT(QUARTER FROM d)::SMALLINT,
    EXTRACT(MONTH FROM d)::SMALLINT,
    TO_CHAR(d, 'TMMonth'),
    UPPER(SUBSTRING(TO_CHAR(d, 'TMMonth'), 1, 3)),
    EXTRACT(WEEK FROM d)::SMALLINT,
    EXTRACT(DAY FROM d)::SMALLINT,
    EXTRACT(DOW FROM d)::SMALLINT,
    TO_CHAR(d, 'TMDay'),
    UPPER(SUBSTRING(TO_CHAR(d, 'TMDay'), 1, 3)),
    EXTRACT(DOW FROM d) IN (0, 6),
    EXTRACT(DOW FROM d) NOT IN (0, 6)
FROM generate_series('2010-01-01'::DATE, '2026-12-31'::DATE, '1 day') AS d
ON CONFLICT (data) DO NOTHING;

-- Enriquecer com feriados (após carga do bronze_feriados)
-- UPDATE gold.dim_tempo t SET eh_feriado = TRUE, nome_feriado = f.nome_feriado,
--   tipo_feriado = f.tipo, eh_dia_util = FALSE
-- FROM bronze.feriados f WHERE t.data = f.data::DATE;

-- ── dim_cliente ───────────────────────────────────────────────────
-- SCD Tipo 2: mantém histórico de mudanças de endereço, renda, score
CREATE TABLE IF NOT EXISTS gold.dim_cliente (
    sk_cliente          SERIAL          PRIMARY KEY,
    cod_cliente         INTEGER         NOT NULL,
    -- Dados pessoais
    primeiro_nome       VARCHAR(100)    NOT NULL,
    ultimo_nome         VARCHAR(100)    NOT NULL,
    nome_completo       VARCHAR(200)    GENERATED ALWAYS AS (primeiro_nome || ' ' || ultimo_nome) STORED,
    cpf                 CHAR(14),       -- XXX.XXX.XXX-XX
    cnpj                CHAR(18),       -- XX.XXX.XXX/XXXX-XX
    tipo_pessoa         CHAR(2)         NOT NULL DEFAULT 'PF',  -- PF, PJ
    email               VARCHAR(200),
    -- Dados demográficos
    data_nascimento     DATE,
    idade               SMALLINT,
    faixa_etaria        VARCHAR(20),    -- '18-24','25-34','35-44','45-54','55-64','65+'
    sexo                CHAR(1),        -- M, F, O
    -- Dados financeiros (SCD2 — mudam ao longo do tempo)
    renda_mensal        NUMERIC(12,2),
    faixa_renda         VARCHAR(20),    -- '<2k','2-5k','5-10k','10-20k','>20k'
    profissao           VARCHAR(100),
    escolaridade        VARCHAR(50),    -- 'Fundamental','Médio','Superior','Pós-graduação'
    score_credito       SMALLINT,       -- 0-1000
    faixa_score         VARCHAR(20),    -- 'Muito Baixo','Baixo','Regular','Bom','Excelente'
    -- Localização
    cep                 CHAR(9),
    logradouro          VARCHAR(200),
    cidade              VARCHAR(100),
    uf                  CHAR(2),
    sk_municipio        INTEGER,        -- FK → dim_municipio
    -- SCD2 fields
    data_inclusao       DATE            NOT NULL,
    data_inicio_vigencia DATE           NOT NULL DEFAULT CURRENT_DATE,
    data_fim_vigencia   DATE            DEFAULT '9999-12-31',
    eh_registro_atual   BOOLEAN         NOT NULL DEFAULT TRUE,
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── dim_agencia ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_agencia (
    sk_agencia          SERIAL          PRIMARY KEY,
    cod_agencia         INTEGER         NOT NULL UNIQUE,
    nome                VARCHAR(200)    NOT NULL,
    tipo_agencia        VARCHAR(20)     NOT NULL,  -- Física, Digital, Premium, Corporate
    -- Localização
    endereco            VARCHAR(300),
    cidade              VARCHAR(100)    NOT NULL,
    uf                  CHAR(2)         NOT NULL,
    cep                 CHAR(9),
    sk_municipio        INTEGER,        -- FK → dim_municipio
    latitude            NUMERIC(10,7),
    longitude           NUMERIC(10,7),
    -- Negócio
    data_abertura       DATE            NOT NULL,
    data_encerramento   DATE,           -- NULL = ativa
    eh_ativa            BOOLEAN         NOT NULL DEFAULT TRUE,
    meta_comercial_mensal NUMERIC(14,2),
    regiao              VARCHAR(20),    -- Norte, Nordeste, Centro-Oeste, Sudeste, Sul
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── dim_colaborador ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_colaborador (
    sk_colaborador      SERIAL          PRIMARY KEY,
    cod_colaborador     INTEGER         NOT NULL,
    primeiro_nome       VARCHAR(100)    NOT NULL,
    ultimo_nome         VARCHAR(100)    NOT NULL,
    nome_completo       VARCHAR(200)    GENERATED ALWAYS AS (primeiro_nome || ' ' || ultimo_nome) STORED,
    cpf                 CHAR(14),
    email               VARCHAR(200),
    data_nascimento     DATE,
    idade               SMALLINT,
    -- Dados profissionais
    cargo               VARCHAR(100),   -- Gerente, Analista, Assistente, Diretor
    departamento        VARCHAR(100),   -- Crédito, Operações, Comercial, TI
    nivel_hierarquico   SMALLINT,       -- 1=Diretor, 2=Gerente, 3=Analista, 4=Assistente
    salario_base        NUMERIC(10,2),
    data_admissao       DATE,
    data_demissao       DATE,
    eh_ativo            BOOLEAN         NOT NULL DEFAULT TRUE,
    -- Localização
    sk_agencia_principal INTEGER,       -- FK → dim_agencia
    cidade              VARCHAR(100),
    uf                  CHAR(2),
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── dim_municipio (localidade enriquecida) ────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_municipio (
    sk_municipio        SERIAL          PRIMARY KEY,
    codigo_ibge         INTEGER         NOT NULL UNIQUE,
    municipio           VARCHAR(150)    NOT NULL,
    uf                  CHAR(2)         NOT NULL,
    uf_nome             VARCHAR(50),
    regiao              VARCHAR(20),    -- Norte, Nordeste, Centro-Oeste, Sudeste, Sul
    regiao_sigla        CHAR(2),
    -- Dados demográficos (Censo 2022)
    populacao           INTEGER,
    ano_populacao       SMALLINT,
    densidade_pop       NUMERIC(10,2),  -- hab/km²
    porte_municipio     VARCHAR(20),    -- Pequeno(<20k), Médio, Grande, Metrópole(>1M)
    -- Dados econômicos (PIB 2021)
    pib_total           BIGINT,         -- R$
    pib_per_capita      NUMERIC(14,2),  -- R$
    ano_pib             SMALLINT,
    faixa_pib_per_cap   VARCHAR(20),    -- '<10k','10-25k','25-50k','>50k'
    -- Dados sociais (a preencher)
    renda_media         NUMERIC(10,2),  -- R$ médio per capita
    taxa_escolaridade   NUMERIC(5,2),   -- % com ensino médio completo
    idhm                NUMERIC(5,3),   -- 0-1
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── dim_produto (generalizada) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_produto (
    sk_produto          SERIAL          PRIMARY KEY,
    cod_produto         VARCHAR(20)     NOT NULL UNIQUE,
    nome_produto        VARCHAR(100)    NOT NULL,
    categoria           VARCHAR(50)     NOT NULL,  -- Conta, Crédito, Investimento, Seguro, Cartão
    subcategoria        VARCHAR(50),
    -- Atributos financeiros
    indexador           VARCHAR(20),    -- CDI, IPCA, Prefixado, Selic
    taxa_base           NUMERIC(8,4),
    prazo_minimo_dias   INTEGER,
    prazo_maximo_dias   INTEGER,
    valor_minimo        NUMERIC(14,2),
    -- Classificações
    risco               VARCHAR(20),    -- Baixo, Médio, Alto
    liquidez            VARCHAR(20),    -- Diária, D+1, D+30, No vencimento
    garantia_fgc        BOOLEAN         DEFAULT FALSE,
    -- Metadados
    eh_ativo            BOOLEAN         NOT NULL DEFAULT TRUE,
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- Inserir produtos padrão BanVic
INSERT INTO gold.dim_produto (cod_produto, nome_produto, categoria, subcategoria, indexador, risco, liquidez, garantia_fgc)
VALUES
    -- Contas
    ('CORR_PF', 'Conta Corrente PF', 'Conta', 'Corrente', NULL, 'Baixo', 'Diária', FALSE),
    ('CORR_PJ', 'Conta Corrente PJ', 'Conta', 'Corrente', NULL, 'Baixo', 'Diária', FALSE),
    ('POUPP',   'Conta Poupança', 'Conta', 'Poupança', 'Poupança', 'Baixo', 'Diária', TRUE),
    ('SALARIO', 'Conta Salário', 'Conta', 'Salário', NULL, 'Baixo', 'Diária', FALSE),
    -- Crédito
    ('EMPREST_PESS', 'Empréstimo Pessoal', 'Crédito', 'Empréstimo', 'Prefixado', 'Médio', NULL, FALSE),
    ('CONSIG',       'Crédito Consignado', 'Crédito', 'Consignado', 'Prefixado', 'Baixo', NULL, FALSE),
    ('FINANC_AUTO',  'Financiamento Auto', 'Crédito', 'Financiamento', 'Prefixado', 'Médio', NULL, FALSE),
    ('FINANC_IMOB',  'Financiamento Imobiliário', 'Crédito', 'Financiamento', 'IPCA+', 'Médio', NULL, FALSE),
    ('LIMITE_CC',    'Limite Conta Corrente', 'Crédito', 'Cheque Especial', 'Prefixado', 'Alto', NULL, FALSE),
    -- Investimentos
    ('CDB_PRE',  'CDB Pré-fixado', 'Investimento', 'CDB', 'Prefixado', 'Baixo', 'No vencimento', TRUE),
    ('CDB_CDI',  'CDB % CDI', 'Investimento', 'CDB', 'CDI', 'Baixo', 'D+1', TRUE),
    ('LCI',      'LCI', 'Investimento', 'LCI', 'CDI', 'Baixo', 'No vencimento', TRUE),
    ('LCA',      'LCA', 'Investimento', 'LCA', 'CDI', 'Baixo', 'No vencimento', TRUE),
    ('FUNDO_RF', 'Fundo Renda Fixa', 'Investimento', 'Fundo', 'CDI', 'Baixo', 'D+1', FALSE),
    ('FUNDO_MM', 'Fundo Multimercado', 'Investimento', 'Fundo', 'CDI', 'Médio', 'D+30', FALSE),
    ('FUNDO_AV', 'Fundo de Ações', 'Investimento', 'Fundo', 'IBOV', 'Alto', 'D+30', FALSE),
    ('TESOURO_S', 'Tesouro Selic', 'Investimento', 'Tesouro', 'Selic', 'Baixo', 'D+1', FALSE),
    ('TESOURO_I', 'Tesouro IPCA+', 'Investimento', 'Tesouro', 'IPCA+', 'Baixo', 'No vencimento', FALSE),
    ('PREV_PGBL', 'Previdência PGBL', 'Investimento', 'Previdência', 'CDI', 'Médio', 'D+5', FALSE),
    ('ETF_BOVA', 'ETF BOVA11', 'Investimento', 'ETF', 'IBOV', 'Alto', 'Diária', FALSE),
    -- Seguros
    ('SEG_VIDA', 'Seguro de Vida', 'Seguro', 'Vida', NULL, 'Baixo', NULL, FALSE),
    ('SEG_AUTO', 'Seguro Auto', 'Seguro', 'Automóvel', NULL, 'Baixo', NULL, FALSE),
    ('SEG_RESI', 'Seguro Residencial', 'Seguro', 'Residencial', NULL, 'Baixo', NULL, FALSE),
    ('SEG_EMPR', 'Seguro Empresarial', 'Seguro', 'Empresarial', NULL, 'Baixo', NULL, FALSE),
    -- Cartões
    ('CART_CRED_BASIC', 'Cartão Crédito Básico', 'Cartão', 'Crédito', NULL, 'Médio', NULL, FALSE),
    ('CART_CRED_GOLD',  'Cartão Crédito Gold', 'Cartão', 'Crédito', NULL, 'Médio', NULL, FALSE),
    ('CART_CRED_PLAT',  'Cartão Crédito Platinum', 'Cartão', 'Crédito', NULL, 'Médio', NULL, FALSE),
    ('CART_DEB',        'Cartão Débito', 'Cartão', 'Débito', NULL, 'Baixo', NULL, FALSE)
ON CONFLICT (cod_produto) DO NOTHING;

-- ── dim_canal ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_canal (
    sk_canal        SERIAL          PRIMARY KEY,
    nome_canal      VARCHAR(50)     NOT NULL UNIQUE,
    tipo_canal      VARCHAR(30),    -- Digital, Presencial, ATM
    subtipo         VARCHAR(50),    -- App, Internet Banking, Agência, Caixa Eletrônico
    eh_digital      BOOLEAN         NOT NULL DEFAULT TRUE
);

INSERT INTO gold.dim_canal (nome_canal, tipo_canal, subtipo, eh_digital) VALUES
    ('Pix',               'Digital', 'App/IB', TRUE),
    ('TED',               'Digital', 'App/IB', TRUE),
    ('DOC',               'Digital', 'App/IB', TRUE),
    ('Compra Crédito',    'Digital', 'Cartão', TRUE),
    ('Compra Débito',     'Digital', 'Cartão', TRUE),
    ('Pagamento Boleto',  'Digital', 'App/IB', TRUE),
    ('Saque',             'Presencial', 'ATM/Caixa', FALSE),
    ('Depósito Espécie',  'Presencial', 'Caixa', FALSE),
    ('Transferência CC',  'Digital', 'App/IB', TRUE),
    ('Estorno',           'Digital', 'Sistema', TRUE),
    ('IOF',               'Digital', 'Sistema', TRUE),
    ('Tarifa',            'Digital', 'Sistema', TRUE)
ON CONFLICT (nome_canal) DO NOTHING;

-- ── dim_score_credito ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.dim_score_credito (
    sk_score        SERIAL          PRIMARY KEY,
    faixa_score     VARCHAR(20)     NOT NULL UNIQUE,
    score_min       SMALLINT        NOT NULL,
    score_max       SMALLINT        NOT NULL,
    classificacao   VARCHAR(20)     NOT NULL,  -- Muito Baixo, Baixo, Regular, Bom, Excelente
    risco           VARCHAR(10)     NOT NULL,  -- Alto, Médio, Baixo
    taxa_min_mes    NUMERIC(6,4),
    taxa_max_mes    NUMERIC(6,4)
);

INSERT INTO gold.dim_score_credito (faixa_score, score_min, score_max, classificacao, risco, taxa_min_mes, taxa_max_mes)
VALUES
    ('0-300',   0,   300, 'Muito Baixo', 'Alto',  0.0300, 0.3000),
    ('301-500', 301, 500, 'Baixo',       'Alto',  0.0200, 0.0300),
    ('501-700', 501, 700, 'Regular',     'Médio', 0.0100, 0.0200),
    ('701-850', 701, 850, 'Bom',         'Baixo', 0.0060, 0.0100),
    ('851-1000',851,1000, 'Excelente',   'Baixo', 0.0030, 0.0060)
ON CONFLICT (faixa_score) DO NOTHING;


-- ================================================================
-- FATOS
-- ================================================================

-- ── fato_transacoes ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_transacoes (
    sk_transacao        BIGSERIAL       PRIMARY KEY,
    cod_transacao       INTEGER         NOT NULL,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_agencia          INTEGER         NOT NULL REFERENCES gold.dim_agencia(sk_agencia),
    sk_canal            INTEGER         REFERENCES gold.dim_canal(sk_canal),
    -- Conta
    num_conta           INTEGER         NOT NULL,
    nome_transacao      VARCHAR(100),
    -- Medidas
    valor_transacao     NUMERIC(14,2)   NOT NULL,
    valor_absoluto      NUMERIC(14,2)   GENERATED ALWAYS AS (ABS(valor_transacao)) STORED,
    flag_credito        BOOLEAN         NOT NULL,  -- TRUE = entrada, FALSE = saída
    -- Câmbio (para converter em USD na data)
    valor_usd           NUMERIC(14,4),
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── fato_contas (snapshot corrente — 1 linha por conta) ──────────
CREATE TABLE IF NOT EXISTS gold.fato_contas (
    sk_conta_snap       BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),  -- data do ultimo snapshot
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_agencia          INTEGER         NOT NULL REFERENCES gold.dim_agencia(sk_agencia),
    sk_colaborador      INTEGER         REFERENCES gold.dim_colaborador(sk_colaborador),
    sk_produto          INTEGER         REFERENCES gold.dim_produto(sk_produto),
    -- Conta
    num_conta           INTEGER         NOT NULL,
    -- Medidas
    saldo_total         NUMERIC(14,2),
    saldo_disponivel    NUMERIC(14,2),
    qtd_transacoes_mes  INTEGER,
    volume_creditos     NUMERIC(14,2),
    volume_debitos      NUMERIC(14,2),
    eh_conta_ativa      BOOLEAN         DEFAULT TRUE,
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (num_conta)
);

-- ── fato_propostas_credito ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_propostas_credito (
    sk_proposta         SERIAL          PRIMARY KEY,
    cod_proposta        INTEGER         NOT NULL,
    -- Dimensões temporais
    sk_tempo_entrada    INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),
    sk_tempo_decisao    INTEGER         REFERENCES gold.dim_tempo(sk_tempo),
    -- Dimensões
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_colaborador      INTEGER         REFERENCES gold.dim_colaborador(sk_colaborador),
    sk_produto          INTEGER         REFERENCES gold.dim_produto(sk_produto),
    -- Medidas
    valor_proposta      NUMERIC(14,2)   NOT NULL,
    valor_financiamento NUMERIC(14,2),
    valor_entrada       NUMERIC(14,2),
    valor_prestacao     NUMERIC(14,2),
    taxa_juros_mensal   NUMERIC(8,6),
    quantidade_parcelas SMALLINT,
    carencia_dias       SMALLINT,
    -- Status
    status_proposta     VARCHAR(50)     NOT NULL,
    dias_decisao        INTEGER,        -- dias entre entrada e decisão
    motivo_recusa       VARCHAR(200),
    flag_inadimplente   BOOLEAN         DEFAULT FALSE,
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── fato_investimentos ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_investimentos (
    sk_investimento     BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_produto          INTEGER         NOT NULL REFERENCES gold.dim_produto(sk_produto),
    sk_agencia          INTEGER         REFERENCES gold.dim_agencia(sk_agencia),
    -- Dados do investimento
    data_aplicacao      DATE            NOT NULL,
    data_vencimento     DATE,
    -- Medidas financeiras
    valor_aplicado      NUMERIC(14,2)   NOT NULL,
    valor_atual         NUMERIC(14,2),
    rentabilidade_pct   NUMERIC(8,4),   -- % no período
    rentabilidade_cdi   NUMERIC(8,4),   -- % do CDI
    -- Status
    status              VARCHAR(20)     NOT NULL DEFAULT 'Ativo',  -- Ativo, Resgatado, Vencido
    data_resgate        DATE,
    valor_resgate       NUMERIC(14,2),
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── fato_cartoes ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_cartoes (
    sk_fatura           BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),  -- mês de referência
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_produto          INTEGER         NOT NULL REFERENCES gold.dim_produto(sk_produto),
    sk_agencia          INTEGER         REFERENCES gold.dim_agencia(sk_agencia),
    -- Dados do cartão
    num_cartao_hash     CHAR(64),       -- SHA256 do número — nunca armazenar número real
    -- Medidas
    limite_total        NUMERIC(12,2)   NOT NULL,
    limite_disponivel   NUMERIC(12,2),
    gasto_mes           NUMERIC(12,2),
    valor_fatura        NUMERIC(12,2),
    valor_minimo_pago   NUMERIC(12,2),
    valor_pago          NUMERIC(12,2),
    valor_parcelado     NUMERIC(12,2),
    qtd_parcelas        SMALLINT,
    dias_atraso         SMALLINT        DEFAULT 0,
    -- Taxas
    taxa_rotativo_mes   NUMERIC(6,4),
    taxa_parcelamento   NUMERIC(6,4),
    -- Utilização
    pct_utilizacao      NUMERIC(5,2)    GENERATED ALWAYS AS
                        (CASE WHEN limite_total > 0 THEN gasto_mes / limite_total * 100 ELSE 0 END) STORED,
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (sk_cliente, sk_produto, sk_tempo)
);

-- ── fato_seguros ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_seguros (
    sk_apolice          BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),  -- mês de vigência
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_produto          INTEGER         NOT NULL REFERENCES gold.dim_produto(sk_produto),
    sk_agencia          INTEGER         REFERENCES gold.dim_agencia(sk_agencia),
    -- Dados da apólice
    num_apolice         VARCHAR(30)     NOT NULL,
    data_inicio         DATE            NOT NULL,
    data_fim            DATE,
    -- Medidas
    valor_segurado      NUMERIC(14,2),
    premio_mensal       NUMERIC(10,2)   NOT NULL,
    valor_sinistro      NUMERIC(14,2)   DEFAULT 0,
    -- Status
    status_apolice      VARCHAR(20)     NOT NULL DEFAULT 'Ativa',  -- Ativa, Cancelada, Sinistrada
    motivo_cancelamento VARCHAR(200),
    -- Cross-sell
    foi_cross_sell      BOOLEAN         DEFAULT FALSE,  -- vendido junto com outro produto?
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── fato_inadimplencia ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_inadimplencia (
    sk_inadimplencia    BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_produto          INTEGER         REFERENCES gold.dim_produto(sk_produto),
    -- Contrato
    cod_contrato        VARCHAR(30)     NOT NULL,  -- cod_proposta, num_cartao, etc.
    tipo_contrato       VARCHAR(30)     NOT NULL,  -- Crédito, Cartão, Financiamento
    -- Medidas
    valor_total_contrato NUMERIC(14,2),
    valor_aberto        NUMERIC(14,2)   NOT NULL,  -- valor em atraso
    dias_atraso         INTEGER         NOT NULL,
    bucket              VARCHAR(10)     NOT NULL,  -- '0-30','31-60','61-90','90+'
    -- Score e risco no momento
    score_credito       SMALLINT,
    faixa_risco         VARCHAR(20),   -- Baixo, Médio, Alto, Crítico
    -- Recuperação
    valor_recuperado    NUMERIC(14,2)   DEFAULT 0,
    flag_write_off      BOOLEAN         DEFAULT FALSE,
    data_write_off      DATE,
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── fato_fraudes ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_fraudes (
    sk_fraude           BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),
    sk_cliente          INTEGER         NOT NULL REFERENCES gold.dim_cliente(sk_cliente),
    sk_canal            INTEGER         REFERENCES gold.dim_canal(sk_canal),
    sk_agencia          INTEGER         REFERENCES gold.dim_agencia(sk_agencia),
    -- Dados da ocorrência
    cod_transacao_suspeita INTEGER,
    hora_ocorrencia     TIME,
    -- Localização da fraude
    cidade_fraude       VARCHAR(100),
    uf_fraude           CHAR(2),
    ip_hash             CHAR(64),       -- SHA256
    dispositivo         VARCHAR(50),    -- Mobile, Desktop, ATM, POS
    -- Medidas
    valor_fraude        NUMERIC(14,2)   NOT NULL,
    valor_recuperado    NUMERIC(14,2)   DEFAULT 0,
    -- Classificação
    flag_tentativa      BOOLEAN         NOT NULL DEFAULT TRUE,
    flag_confirmada     BOOLEAN         NOT NULL DEFAULT FALSE,
    tipo_fraude         VARCHAR(50),    -- Phishing, Clonagem, Engenharia Social, Invasão conta
    -- Metadados
    data_deteccao       TIMESTAMP,
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ── fato_receitas ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gold.fato_receitas (
    sk_receita          BIGSERIAL       PRIMARY KEY,
    -- Dimensões
    sk_tempo            INTEGER         NOT NULL REFERENCES gold.dim_tempo(sk_tempo),
    sk_agencia          INTEGER         NOT NULL REFERENCES gold.dim_agencia(sk_agencia),
    sk_produto          INTEGER         REFERENCES gold.dim_produto(sk_produto),
    -- Classificação
    tipo_receita        VARCHAR(50)     NOT NULL,   -- Juros, Tarifa, Seguro, Investimento, Cartão
    -- Medidas
    valor_receita       NUMERIC(14,2)   NOT NULL,
    valor_custo         NUMERIC(14,2)   DEFAULT 0,
    margem              NUMERIC(14,2)   GENERATED ALWAYS AS (valor_receita - valor_custo) STORED,
    -- Metadados
    _carga_ts           TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);


-- ================================================================
-- ÍNDICES DE PERFORMANCE
-- ================================================================

-- dim_tempo
CREATE INDEX IF NOT EXISTS idx_dim_tempo_ano_mes       ON gold.dim_tempo(ano, mes);
CREATE INDEX IF NOT EXISTS idx_dim_tempo_eh_dia_util   ON gold.dim_tempo(eh_dia_util);
CREATE INDEX IF NOT EXISTS idx_dim_tempo_selic         ON gold.dim_tempo(taxa_selic);

-- dim_cliente
CREATE INDEX IF NOT EXISTS idx_dim_cli_cod             ON gold.dim_cliente(cod_cliente);
CREATE INDEX IF NOT EXISTS idx_dim_cli_cpf             ON gold.dim_cliente(cpf);
CREATE INDEX IF NOT EXISTS idx_dim_cli_uf              ON gold.dim_cliente(uf);
CREATE INDEX IF NOT EXISTS idx_dim_cli_municipio       ON gold.dim_cliente(sk_municipio);
CREATE INDEX IF NOT EXISTS idx_dim_cli_faixa_renda     ON gold.dim_cliente(faixa_renda);
CREATE INDEX IF NOT EXISTS idx_dim_cli_vigencia        ON gold.dim_cliente(eh_registro_atual);

-- dim_agencia
CREATE INDEX IF NOT EXISTS idx_dim_ag_uf               ON gold.dim_agencia(uf);
CREATE INDEX IF NOT EXISTS idx_dim_ag_regiao           ON gold.dim_agencia(regiao);
CREATE INDEX IF NOT EXISTS idx_dim_ag_tipo             ON gold.dim_agencia(tipo_agencia);

-- dim_municipio
CREATE INDEX IF NOT EXISTS idx_dim_mun_ibge            ON gold.dim_municipio(codigo_ibge);
CREATE INDEX IF NOT EXISTS idx_dim_mun_uf              ON gold.dim_municipio(uf);
CREATE INDEX IF NOT EXISTS idx_dim_mun_regiao          ON gold.dim_municipio(regiao);

-- fato_transacoes
CREATE INDEX IF NOT EXISTS idx_ft_tempo                ON gold.fato_transacoes(sk_tempo);
CREATE INDEX IF NOT EXISTS idx_ft_cliente              ON gold.fato_transacoes(sk_cliente);
CREATE INDEX IF NOT EXISTS idx_ft_agencia              ON gold.fato_transacoes(sk_agencia);
CREATE INDEX IF NOT EXISTS idx_ft_canal                ON gold.fato_transacoes(sk_canal);
CREATE INDEX IF NOT EXISTS idx_ft_conta                ON gold.fato_transacoes(num_conta);

-- fato_contas
CREATE INDEX IF NOT EXISTS idx_fc_tempo                ON gold.fato_contas(sk_tempo);
CREATE INDEX IF NOT EXISTS idx_fc_cliente              ON gold.fato_contas(sk_cliente);
CREATE INDEX IF NOT EXISTS idx_fc_agencia              ON gold.fato_contas(sk_agencia);

-- fato_propostas
CREATE INDEX IF NOT EXISTS idx_fp_tempo                ON gold.fato_propostas_credito(sk_tempo_entrada);
CREATE INDEX IF NOT EXISTS idx_fp_cliente              ON gold.fato_propostas_credito(sk_cliente);
CREATE INDEX IF NOT EXISTS idx_fp_status               ON gold.fato_propostas_credito(status_proposta);

-- fato_inadimplencia
CREATE INDEX IF NOT EXISTS idx_fi_tempo                ON gold.fato_inadimplencia(sk_tempo);
CREATE INDEX IF NOT EXISTS idx_fi_cliente              ON gold.fato_inadimplencia(sk_cliente);
CREATE INDEX IF NOT EXISTS idx_fi_bucket               ON gold.fato_inadimplencia(bucket);


-- ================================================================
-- VIEWS ANALÍTICAS — 8 KPIs DO GABARITO
-- ================================================================

-- KPI 1: Saldo sob gestão por agência
CREATE OR REPLACE VIEW gold.vw_kpi1_saldo_por_agencia AS
SELECT
    a.cod_agencia,
    a.nome                              AS nome_agencia,
    a.tipo_agencia,
    a.cidade,
    a.uf,
    COUNT(DISTINCT fc.num_conta)        AS qtd_contas,
    SUM(fc.saldo_total)                 AS saldo_total,
    SUM(fc.saldo_disponivel)            AS saldo_disponivel,
    AVG(fc.saldo_total)                 AS saldo_medio
FROM gold.fato_contas fc
JOIN gold.dim_agencia a     ON a.sk_agencia = fc.sk_agencia
JOIN gold.dim_tempo t       ON t.sk_tempo = fc.sk_tempo
WHERE fc.eh_conta_ativa = TRUE
GROUP BY a.cod_agencia, a.nome, a.tipo_agencia, a.cidade, a.uf
ORDER BY saldo_total DESC;

-- KPI 2 e 3: Volume e mix de transações por mês
CREATE OR REPLACE VIEW gold.vw_kpi2_3_transacoes_por_mes AS
SELECT
    t.ano,
    t.mes,
    t.mes_nome,
    ft.nome_transacao,
    COUNT(*)                            AS qtd_transacoes,
    SUM(ft.valor_absoluto)              AS volume_total,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY t.ano, t.mes), 2) AS pct_mix
FROM gold.fato_transacoes ft
JOIN gold.dim_tempo t       ON t.sk_tempo = ft.sk_tempo
GROUP BY t.ano, t.mes, t.mes_nome, ft.nome_transacao
ORDER BY t.ano, t.mes, volume_total DESC;

-- KPI 4: Conversão de propostas (agrupado por status -- nivel total)
CREATE OR REPLACE VIEW gold.vw_kpi4_conversao_propostas AS
SELECT
    fp.status_proposta,
    COUNT(*)                            AS qtd_propostas,
    SUM(fp.valor_proposta)              AS valor_total_proposto,
    SUM(fp.valor_financiamento)         AS valor_total_financiado,
    AVG(fp.taxa_juros_mensal * 100)     AS taxa_media_pct,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_status
FROM gold.fato_propostas_credito fp
GROUP BY fp.status_proposta
ORDER BY qtd_propostas DESC;

-- KPI 5: Ranking de agencias (saldo + volume)
CREATE OR REPLACE VIEW gold.vw_kpi5_ranking_agencias AS
WITH volume_ag AS (
    SELECT a.cod_agencia,
           SUM(ft.valor_absoluto) AS volume_total
    FROM gold.fato_transacoes ft
    JOIN gold.dim_agencia a ON a.sk_agencia = ft.sk_agencia
    GROUP BY a.cod_agencia
)
SELECT
    ROW_NUMBER() OVER (ORDER BY k1.saldo_total DESC, COALESCE(v.volume_total, 0) DESC) AS ranking,
    k1.cod_agencia, k1.nome_agencia, k1.tipo_agencia, k1.cidade, k1.uf,
    k1.qtd_contas, k1.saldo_total, k1.saldo_medio,
    COALESCE(v.volume_total, 0) AS volume_total
FROM gold.vw_kpi1_saldo_por_agencia k1
LEFT JOIN volume_ag v ON v.cod_agencia = k1.cod_agencia;

-- KPI 6: Carteira por colaborador
CREATE OR REPLACE VIEW gold.vw_kpi6_carteira_colaborador AS
WITH contas_por_col AS (
    SELECT sk_colaborador,
           COUNT(DISTINCT num_conta) AS qtd_contas,
           SUM(saldo_total)          AS saldo_total
    FROM gold.fato_contas
    WHERE eh_conta_ativa = TRUE
    GROUP BY sk_colaborador
),
propostas_por_col AS (
    SELECT sk_colaborador,
           COUNT(DISTINCT cod_proposta)                                              AS qtd_propostas,
           COUNT(DISTINCT cod_proposta) FILTER (WHERE status_proposta = 'Aprovada') AS propostas_aprovadas
    FROM gold.fato_propostas_credito
    GROUP BY sk_colaborador
)
SELECT
    col.cod_colaborador,
    col.nome_completo,
    col.cargo,
    a.nome                                  AS agencia,
    COALESCE(cc.qtd_contas, 0)              AS qtd_contas_geridas,
    COALESCE(cc.saldo_total, 0)             AS saldo_gerido,
    COALESCE(pc.qtd_propostas, 0)           AS qtd_propostas,
    COALESCE(pc.propostas_aprovadas, 0)     AS propostas_aprovadas
FROM gold.dim_colaborador col
JOIN gold.dim_agencia a         ON a.sk_agencia = col.sk_agencia_principal
LEFT JOIN contas_por_col cc     ON cc.sk_colaborador = col.sk_colaborador
LEFT JOIN propostas_por_col pc  ON pc.sk_colaborador = col.sk_colaborador
WHERE col.eh_ativo = TRUE
ORDER BY saldo_gerido DESC NULLS LAST;

-- KPI 7: Segmentação de clientes por faixa etária
CREATE OR REPLACE VIEW gold.vw_kpi7_segmentacao_clientes AS
SELECT
    cli.faixa_etaria,
    COUNT(DISTINCT cli.sk_cliente)       AS qtd_clientes,
    AVG(fc.saldo_total)                  AS saldo_medio,
    SUM(fc.saldo_total)                  AS saldo_total,
    AVG(cli.score_credito)               AS score_medio,
    COUNT(DISTINCT fc.num_conta)         AS qtd_contas
FROM gold.dim_cliente cli
LEFT JOIN gold.fato_contas fc ON fc.sk_cliente = cli.sk_cliente AND fc.eh_conta_ativa = TRUE
WHERE cli.eh_registro_atual = TRUE
GROUP BY cli.faixa_etaria
ORDER BY cli.faixa_etaria;

-- KPI 8: Correção IPCA
CREATE OR REPLACE VIEW gold.vw_kpi8_correcao_ipca AS
WITH base_ipca AS (
    SELECT indice_ipca FROM gold.dim_tempo
    WHERE data = (SELECT MAX(data) FROM gold.dim_tempo WHERE indice_ipca IS NOT NULL)
    LIMIT 1
)
SELECT
    t.ano,
    t.mes,
    t.mes_nome,
    t.indice_ipca                        AS indice_mes,
    b.indice_ipca                        AS indice_base,
    SUM(ABS(ft.valor_transacao))         AS volume_nominal,
    ROUND(SUM(ABS(ft.valor_transacao)) * b.indice_ipca / NULLIF(t.indice_ipca, 0), 2)
                                         AS volume_real_moeda_atual
FROM gold.fato_transacoes ft
JOIN gold.dim_tempo t ON t.sk_tempo = ft.sk_tempo
CROSS JOIN base_ipca b
WHERE t.indice_ipca IS NOT NULL
GROUP BY t.ano, t.mes, t.mes_nome, t.indice_ipca, b.indice_ipca
ORDER BY t.ano, t.mes;
