-- ================================================================
-- BanVic 360 -- DDL Bronze Layer
-- ================================================================
-- Tabelas de ingestao bruta: todos os campos como TEXT.
-- Nenhuma transformacao aqui -- dados exatamente como vieram da fonte.
-- Executar apos 00_schemas_extensoes.sql
-- ================================================================

-- ── BANVIC ORIGINAL (data/banvic/) ──────────────────────────────

CREATE TABLE IF NOT EXISTS bronze.clientes (
    cod_cliente     TEXT,
    primeiro_nome   TEXT,
    ultimo_nome     TEXT,
    email           TEXT,
    tipo_cliente    TEXT,
    data_inclusao   TEXT,
    cpfcnpj         TEXT,
    data_nascimento TEXT,
    endereco        TEXT,
    cep             TEXT,
    _fonte          TEXT DEFAULT 'banvic_original',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.contas (
    num_conta               TEXT,
    cod_cliente             TEXT,
    cod_agencia             TEXT,
    cod_colaborador         TEXT,
    tipo_conta              TEXT,
    data_abertura           TEXT,
    saldo_total             TEXT,
    saldo_disponivel        TEXT,
    data_ultimo_lancamento  TEXT,
    _fonte                  TEXT DEFAULT 'banvic_original',
    _carga_ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.agencias (
    cod_agencia     TEXT,
    nome            TEXT,
    endereco        TEXT,
    cidade          TEXT,
    uf              TEXT,
    data_abertura   TEXT,
    tipo_agencia    TEXT,
    _fonte          TEXT DEFAULT 'banvic_original',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.colaboradores (
    cod_colaborador TEXT,
    primeiro_nome   TEXT,
    ultimo_nome     TEXT,
    email           TEXT,
    cpf             TEXT,
    data_nascimento TEXT,
    endereco        TEXT,
    cep             TEXT,
    _fonte          TEXT DEFAULT 'banvic_original',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.colaborador_agencia (
    cod_colaborador TEXT,
    cod_agencia     TEXT,
    _fonte          TEXT DEFAULT 'banvic_original',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.propostas_credito (
    cod_proposta            TEXT,
    cod_cliente             TEXT,
    cod_colaborador         TEXT,
    data_entrada_proposta   TEXT,
    taxa_juros_mensal       TEXT,
    valor_proposta          TEXT,
    valor_financiamento     TEXT,
    valor_entrada           TEXT,
    valor_prestacao         TEXT,
    quantidade_parcelas     TEXT,
    carencia                TEXT,
    status_proposta         TEXT,
    _fonte                  TEXT DEFAULT 'banvic_original',
    _carga_ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.transacoes (
    cod_transacao   TEXT,
    num_conta       TEXT,
    data_transacao  TEXT,
    nome_transacao  TEXT,
    valor_transacao TEXT,
    _fonte          TEXT DEFAULT 'banvic_original',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── DADOS SINTETICOS (data/sintetico/) ──────────────────────────

CREATE TABLE IF NOT EXISTS bronze.agencias_expandidas (
    cod_agencia             TEXT,
    nome                    TEXT,
    tipo_agencia            TEXT,
    endereco                TEXT,
    cidade                  TEXT,
    uf                      TEXT,
    cep                     TEXT,
    regiao                  TEXT,
    data_abertura           TEXT,
    data_encerramento       TEXT,
    eh_ativa                TEXT,
    meta_comercial_mensal   TEXT,
    latitude                TEXT,
    longitude               TEXT,
    _fonte                  TEXT DEFAULT 'sintetico',
    _carga_ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.colaboradores_expandidos (
    cod_colaborador     TEXT,
    primeiro_nome       TEXT,
    ultimo_nome         TEXT,
    email               TEXT,
    cpf                 TEXT,
    data_nascimento     TEXT,
    cidade              TEXT,
    uf                  TEXT,
    regiao              TEXT,
    cargo               TEXT,
    nivel_hierarquico   TEXT,
    departamento        TEXT,
    salario_base        TEXT,
    cod_agencia         TEXT,
    data_admissao       TEXT,
    data_demissao       TEXT,
    eh_ativo            TEXT,
    _fonte              TEXT DEFAULT 'sintetico',
    _carga_ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.clientes_sinteticos (
    cod_cliente     TEXT,
    primeiro_nome   TEXT,
    ultimo_nome     TEXT,
    email           TEXT,
    tipo_cliente    TEXT,
    data_inclusao   TEXT,
    cpfcnpj         TEXT,
    data_nascimento TEXT,
    cidade          TEXT,
    uf              TEXT,
    cep             TEXT,
    renda_mensal    TEXT,
    faixa_renda     TEXT,
    profissao       TEXT,
    escolaridade    TEXT,
    score_credito   TEXT,
    faixa_score     TEXT,
    idade           TEXT,
    faixa_etaria    TEXT,
    _fonte          TEXT DEFAULT 'sintetico',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.contas_sinteticas (
    num_conta               TEXT,
    cod_cliente             TEXT,
    cod_agencia             TEXT,
    cod_colaborador         TEXT,
    tipo_conta              TEXT,
    data_abertura           TEXT,
    saldo_total             TEXT,
    saldo_disponivel        TEXT,
    data_ultimo_lancamento  TEXT,
    flag_ativa              TEXT,
    _fonte                  TEXT DEFAULT 'sintetico',
    _carga_ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.transacoes_sinteticas (
    cod_transacao   TEXT,
    num_conta       TEXT,
    data_transacao  TEXT,
    nome_transacao  TEXT,
    valor_transacao TEXT,
    _fonte          TEXT DEFAULT 'sintetico',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.propostas_sinteticas (
    cod_proposta            TEXT,
    cod_cliente             TEXT,
    cod_colaborador         TEXT,
    data_entrada_proposta   TEXT,
    taxa_juros_mensal       TEXT,
    valor_proposta          TEXT,
    valor_financiamento     TEXT,
    valor_entrada           TEXT,
    valor_prestacao         TEXT,
    quantidade_parcelas     TEXT,
    carencia                TEXT,
    status_proposta         TEXT,
    produto                 TEXT,
    _fonte                  TEXT DEFAULT 'sintetico',
    _carga_ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.investimentos (
    id_investimento TEXT,
    cod_cliente     TEXT,
    cod_agencia     TEXT,
    cod_produto     TEXT,
    nome_produto    TEXT,
    indexador       TEXT,
    data_aplicacao  TEXT,
    data_vencimento TEXT,
    valor_aplicado  TEXT,
    valor_atual     TEXT,
    rentabilidade_pct TEXT,
    status          TEXT,
    data_resgate    TEXT,
    valor_resgate   TEXT,
    _fonte          TEXT DEFAULT 'sintetico',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.cartoes (
    id_fatura           TEXT,
    cod_cliente         TEXT,
    cod_agencia         TEXT,
    cod_produto         TEXT,
    nome_produto        TEXT,
    mes_referencia      TEXT,
    limite_total        TEXT,
    limite_disponivel   TEXT,
    gasto_mes           TEXT,
    valor_fatura        TEXT,
    valor_pago          TEXT,
    valor_parcelado     TEXT,
    qtd_parcelas        TEXT,
    dias_atraso         TEXT,
    taxa_rotativo_mes   TEXT,
    pct_utilizacao      TEXT,
    _fonte              TEXT DEFAULT 'sintetico',
    _carga_ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.seguros (
    id_apolice           TEXT,
    num_apolice          TEXT,
    cod_cliente          TEXT,
    cod_agencia          TEXT,
    cod_produto          TEXT,
    nome_produto         TEXT,
    data_inicio          TEXT,
    data_fim             TEXT,
    valor_segurado       TEXT,
    premio_mensal        TEXT,
    valor_sinistro       TEXT,
    status_apolice       TEXT,
    motivo_cancelamento  TEXT,
    foi_cross_sell       TEXT,
    _fonte               TEXT DEFAULT 'sintetico',
    _carga_ts            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.inadimplencia (
    id_inadimplencia        TEXT,
    cod_contrato            TEXT,
    tipo_contrato           TEXT,
    cod_cliente             TEXT,
    data_referencia         TEXT,
    valor_total_contrato    TEXT,
    valor_aberto            TEXT,
    dias_atraso             TEXT,
    bucket                  TEXT,
    score_credito           TEXT,
    faixa_risco             TEXT,
    valor_recuperado        TEXT,
    flag_write_off          TEXT,
    data_write_off          TEXT,
    _fonte                  TEXT DEFAULT 'sintetico',
    _carga_ts               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.fraudes (
    id_fraude           TEXT,
    cod_cliente         TEXT,
    cod_agencia         TEXT,
    data_ocorrencia     TEXT,
    hora_ocorrencia     TEXT,
    canal               TEXT,
    tipo_fraude         TEXT,
    dispositivo         TEXT,
    uf_fraude           TEXT,
    valor_fraude        TEXT,
    flag_tentativa      TEXT,
    flag_confirmada     TEXT,
    valor_recuperado    TEXT,
    data_deteccao       TEXT,
    _fonte              TEXT DEFAULT 'sintetico',
    _carga_ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── DADOS EXTERNOS (external_data/) ─────────────────────────────

CREATE TABLE IF NOT EXISTS bronze.ipca (
    data            TEXT,
    ano             TEXT,
    mes             TEXT,
    mes_num         TEXT,
    indice          TEXT,
    no_mes          TEXT,
    acumulado_3m    TEXT,
    acumulado_12m   TEXT,
    acumulado_ano   TEXT,
    _fonte          TEXT DEFAULT 'bcb_sgs',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.selic (
    data        TEXT,
    taxa_selic  TEXT,
    _fonte      TEXT DEFAULT 'bcb_sgs',
    _carga_ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.cdi (
    data      TEXT,
    taxa_cdi  TEXT,
    _fonte    TEXT DEFAULT 'bcb_sgs',
    _carga_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.igpm (
    data              TEXT,
    ano               TEXT,
    mes               TEXT,
    mes_num           TEXT,
    variacao_mensal   TEXT,
    acumulado_12m     TEXT,
    _fonte            TEXT DEFAULT 'bcb_sgs',
    _carga_ts         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.desemprego (
    data                TEXT,
    ano                 TEXT,
    trimestre           TEXT,
    taxa_desemprego_pct TEXT,
    _fonte              TEXT DEFAULT 'bcb_sgs_24369',
    _carga_ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.dolar_ptax (
    data            TEXT,
    cotacao_compra  TEXT,
    cotacao_venda   TEXT,
    cotacao_media   TEXT,
    _fonte          TEXT DEFAULT 'bcb_ptax',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.euro_ptax (
    data            TEXT,
    cotacao_compra  TEXT,
    cotacao_venda   TEXT,
    cotacao_media   TEXT,
    _fonte          TEXT DEFAULT 'bcb_ptax_eur',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.feriados (
    data        TEXT,
    nome        TEXT,
    tipo        TEXT,
    descricao   TEXT,
    _fonte      TEXT DEFAULT 'brasilapi',
    _carga_ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.municipios (
    codigo_ibge TEXT,
    municipio   TEXT,
    uf          TEXT,
    _fonte      TEXT DEFAULT 'ibge_v1',
    _carga_ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.populacao (
    codigo_ibge TEXT,
    municipio   TEXT,
    ano         TEXT,
    populacao   TEXT,
    _fonte      TEXT DEFAULT 'ibge_censo2022',
    _carga_ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.pib_municipal (
    codigo_ibge     TEXT,
    municipio       TEXT,
    ano             TEXT,
    pib_total       TEXT,
    pib_per_capita  TEXT,
    _fonte          TEXT DEFAULT 'ibge_sidra',
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.clima_historico (
    data                TEXT,
    codigo_ibge         TEXT,
    municipio           TEXT,
    uf                  TEXT,
    temperatura_media   TEXT,
    precipitacao_mm     TEXT,
    vento_max_kmh       TEXT,
    _fonte              TEXT DEFAULT 'open_meteo',
    _carga_ts           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── PROJECOES (external_data/projecoes/) ─────────────────────────

CREATE TABLE IF NOT EXISTS bronze.ipca_projetado (
    data            TEXT,
    ano             TEXT,
    mes             TEXT,
    mes_num         TEXT,
    indice          TEXT,
    no_mes          TEXT,
    acumulado_3m    TEXT,
    acumulado_12m   TEXT,
    acumulado_ano   TEXT,
    tipo            TEXT,   -- REAL ou PROJECAO
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.selic_projetada (
    data        TEXT,
    taxa_selic  TEXT,
    tipo        TEXT,
    _carga_ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.cdi_projetado (
    data      TEXT,
    taxa_cdi  TEXT,
    tipo      TEXT,
    _carga_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.populacao_projetada (
    codigo_ibge TEXT,
    municipio   TEXT,
    uf          TEXT,
    ano         TEXT,
    populacao   TEXT,
    tipo        TEXT,
    _carga_ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.pib_projetado (
    codigo_ibge     TEXT,
    municipio       TEXT,
    uf              TEXT,
    ano             TEXT,
    pib_total       TEXT,
    pib_per_capita  TEXT,
    tipo            TEXT,
    _carga_ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
