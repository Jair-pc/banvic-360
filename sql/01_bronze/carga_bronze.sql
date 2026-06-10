-- ================================================================
-- BanVic 360 -- Carga Bronze (COPY commands)
-- ================================================================
-- Ajustar o caminho base conforme seu ambiente.
-- No psql: \set ROOT 'C:/Projeto/ETL e ELT'
-- Executar apos ddl_bronze.sql
-- ================================================================

-- ── Variavel de caminho (ajustar se necessario) ──────────────────
-- \set ROOT 'C:/Projeto/ETL e ELT'

-- ── BANVIC ORIGINAL ──────────────────────────────────────────────

TRUNCATE bronze.clientes;
COPY bronze.clientes (cod_cliente,primeiro_nome,ultimo_nome,email,tipo_cliente,data_inclusao,cpfcnpj,data_nascimento,endereco,cep)
FROM 'C:/Projeto/ETL e ELT/data/banvic/clientes.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.contas;
COPY bronze.contas (num_conta,cod_cliente,cod_agencia,cod_colaborador,tipo_conta,data_abertura,saldo_total,saldo_disponivel,data_ultimo_lancamento)
FROM 'C:/Projeto/ETL e ELT/data/banvic/contas.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.agencias;
COPY bronze.agencias (cod_agencia,nome,endereco,cidade,uf,data_abertura,tipo_agencia)
FROM 'C:/Projeto/ETL e ELT/data/banvic/agencias.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.colaboradores;
COPY bronze.colaboradores (cod_colaborador,primeiro_nome,ultimo_nome,email,cpf,data_nascimento,endereco,cep)
FROM 'C:/Projeto/ETL e ELT/data/banvic/colaboradores.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.colaborador_agencia;
COPY bronze.colaborador_agencia (cod_colaborador,cod_agencia)
FROM 'C:/Projeto/ETL e ELT/data/banvic/colaborador_agencia.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.propostas_credito;
COPY bronze.propostas_credito (cod_proposta,cod_cliente,cod_colaborador,data_entrada_proposta,taxa_juros_mensal,valor_proposta,valor_financiamento,valor_entrada,valor_prestacao,quantidade_parcelas,carencia,status_proposta)
FROM 'C:/Projeto/ETL e ELT/data/banvic/propostas_credito.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.transacoes;
COPY bronze.transacoes (cod_transacao,num_conta,data_transacao,nome_transacao,valor_transacao)
FROM 'C:/Projeto/ETL e ELT/data/banvic/transacoes.csv'
CSV HEADER ENCODING 'UTF8';

-- ── DADOS SINTETICOS ─────────────────────────────────────────────

TRUNCATE bronze.agencias_expandidas;
COPY bronze.agencias_expandidas (cod_agencia,nome,tipo_agencia,endereco,cidade,uf,cep,regiao,data_abertura,data_encerramento,eh_ativa,meta_comercial_mensal,latitude,longitude)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/agencias_expandidas.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.colaboradores_expandidos;
COPY bronze.colaboradores_expandidos (cod_colaborador,primeiro_nome,ultimo_nome,email,cpf,data_nascimento,cidade,uf,regiao,cargo,nivel_hierarquico,departamento,salario_base,cod_agencia,data_admissao,data_demissao,eh_ativo)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/colaboradores_expandidos.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.clientes_sinteticos;
COPY bronze.clientes_sinteticos (cod_cliente,primeiro_nome,ultimo_nome,email,tipo_cliente,data_inclusao,cpfcnpj,data_nascimento,cidade,uf,cep,renda_mensal,faixa_renda,profissao,escolaridade,score_credito,faixa_score,idade,faixa_etaria)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/clientes_sinteticos.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.contas_sinteticas;
COPY bronze.contas_sinteticas (num_conta,cod_cliente,cod_agencia,cod_colaborador,tipo_conta,data_abertura,saldo_total,saldo_disponivel,data_ultimo_lancamento,flag_ativa)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/contas_sinteticas.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.transacoes_sinteticas;
COPY bronze.transacoes_sinteticas (cod_transacao,num_conta,data_transacao,nome_transacao,valor_transacao)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/transacoes_sinteticas.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.propostas_sinteticas;
COPY bronze.propostas_sinteticas (cod_proposta,cod_cliente,cod_colaborador,data_entrada_proposta,taxa_juros_mensal,valor_proposta,valor_financiamento,valor_entrada,valor_prestacao,quantidade_parcelas,carencia,status_proposta,produto)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/propostas_sinteticas.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.investimentos;
COPY bronze.investimentos (id_investimento,cod_cliente,cod_agencia,cod_produto,nome_produto,indexador,data_aplicacao,data_vencimento,valor_aplicado,valor_atual,rentabilidade_pct,status,data_resgate,valor_resgate)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/investimentos.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.cartoes;
COPY bronze.cartoes (id_fatura,cod_cliente,cod_agencia,cod_produto,nome_produto,mes_referencia,limite_total,limite_disponivel,gasto_mes,valor_fatura,valor_pago,valor_parcelado,qtd_parcelas,dias_atraso,taxa_rotativo_mes,pct_utilizacao)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/cartoes.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.seguros;
COPY bronze.seguros (id_apolice,num_apolice,cod_cliente,cod_agencia,cod_produto,nome_produto,data_inicio,data_fim,valor_segurado,premio_mensal,valor_sinistro,status_apolice,motivo_cancelamento,foi_cross_sell)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/seguros.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.inadimplencia;
COPY bronze.inadimplencia (id_inadimplencia,cod_contrato,tipo_contrato,cod_cliente,data_referencia,valor_total_contrato,valor_aberto,dias_atraso,bucket,score_credito,faixa_risco,valor_recuperado,flag_write_off,data_write_off)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/inadimplencia.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.fraudes;
COPY bronze.fraudes (id_fraude,cod_cliente,cod_agencia,data_ocorrencia,hora_ocorrencia,canal,tipo_fraude,dispositivo,uf_fraude,valor_fraude,flag_tentativa,flag_confirmada,valor_recuperado,data_deteccao)
FROM 'C:/Projeto/ETL e ELT/data/sintetico/fraudes.csv'
CSV HEADER ENCODING 'UTF8';

-- ── MACROECONOMIA ────────────────────────────────────────────────

TRUNCATE bronze.ipca;
COPY bronze.ipca (data,ano,mes,mes_num,indice,no_mes,acumulado_3m,acumulado_12m,acumulado_ano)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/ipca.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.selic;
COPY bronze.selic (data,taxa_selic)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/selic.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.cdi;
COPY bronze.cdi (data,taxa_cdi)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/cdi.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.igpm;
COPY bronze.igpm (data,ano,mes,mes_num,variacao_mensal,acumulado_12m)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/igpm.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.desemprego;
COPY bronze.desemprego (data,ano,trimestre,taxa_desemprego_pct)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/desemprego.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.dolar_ptax;
COPY bronze.dolar_ptax (data,cotacao_compra,cotacao_venda,cotacao_media)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/dolar_ptax.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.euro_ptax;
COPY bronze.euro_ptax (data,cotacao_compra,cotacao_venda,cotacao_media)
FROM 'C:/Projeto/ETL e ELT/external_data/macroeconomia/euro_ptax.csv'
CSV HEADER ENCODING 'UTF8';

-- ── CALENDARIO ───────────────────────────────────────────────────

TRUNCATE bronze.feriados;
COPY bronze.feriados (data,nome,tipo,descricao)
FROM 'C:/Projeto/ETL e ELT/external_data/calendario/feriados.csv'
CSV HEADER ENCODING 'UTF8';

-- ── GEOGRAFIA ────────────────────────────────────────────────────

TRUNCATE bronze.municipios;
COPY bronze.municipios (codigo_ibge,municipio,uf)
FROM 'C:/Projeto/ETL e ELT/external_data/geografia/municipios.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.populacao;
COPY bronze.populacao (codigo_ibge,municipio,ano,populacao)
FROM 'C:/Projeto/ETL e ELT/external_data/geografia/populacao.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.pib_municipal;
COPY bronze.pib_municipal (codigo_ibge,municipio,ano,pib_total,pib_per_capita)
FROM 'C:/Projeto/ETL e ELT/external_data/geografia/pib_municipal.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.clima_historico;
COPY bronze.clima_historico (data,codigo_ibge,municipio,uf,temperatura_media,precipitacao_mm,vento_max_kmh)
FROM 'C:/Projeto/ETL e ELT/external_data/clima/clima_historico.csv'
CSV HEADER ENCODING 'UTF8';

-- ── PROJECOES ────────────────────────────────────────────────────

TRUNCATE bronze.ipca_projetado;
COPY bronze.ipca_projetado (data,ano,mes,mes_num,indice,no_mes,acumulado_3m,acumulado_12m,acumulado_ano,tipo)
FROM 'C:/Projeto/ETL e ELT/external_data/projecoes/ipca_projetado.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.selic_projetada;
COPY bronze.selic_projetada (data,taxa_selic,tipo)
FROM 'C:/Projeto/ETL e ELT/external_data/projecoes/selic_projetada.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.cdi_projetado;
COPY bronze.cdi_projetado (data,taxa_cdi,tipo)
FROM 'C:/Projeto/ETL e ELT/external_data/projecoes/cdi_projetado.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.populacao_projetada;
COPY bronze.populacao_projetada (codigo_ibge,municipio,uf,ano,populacao,tipo)
FROM 'C:/Projeto/ETL e ELT/external_data/projecoes/populacao_projetada.csv'
CSV HEADER ENCODING 'UTF8';

TRUNCATE bronze.pib_projetado;
COPY bronze.pib_projetado (codigo_ibge,municipio,uf,ano,pib_total,pib_per_capita,tipo)
FROM 'C:/Projeto/ETL e ELT/external_data/projecoes/pib_projetado.csv'
CSV HEADER ENCODING 'UTF8';

-- ── Verificacao pos-carga ─────────────────────────────────────────

SELECT 'clientes'              AS tabela, COUNT(*) AS linhas FROM bronze.clientes
UNION ALL SELECT 'contas',              COUNT(*) FROM bronze.contas
UNION ALL SELECT 'agencias',            COUNT(*) FROM bronze.agencias
UNION ALL SELECT 'colaboradores',       COUNT(*) FROM bronze.colaboradores
UNION ALL SELECT 'transacoes',          COUNT(*) FROM bronze.transacoes
UNION ALL SELECT 'propostas_credito',   COUNT(*) FROM bronze.propostas_credito
UNION ALL SELECT 'clientes_sinteticos', COUNT(*) FROM bronze.clientes_sinteticos
UNION ALL SELECT 'contas_sinteticas',   COUNT(*) FROM bronze.contas_sinteticas
UNION ALL SELECT 'transacoes_sinteticas',COUNT(*) FROM bronze.transacoes_sinteticas
UNION ALL SELECT 'investimentos',        COUNT(*) FROM bronze.investimentos
UNION ALL SELECT 'cartoes',              COUNT(*) FROM bronze.cartoes
UNION ALL SELECT 'seguros',              COUNT(*) FROM bronze.seguros
UNION ALL SELECT 'inadimplencia',        COUNT(*) FROM bronze.inadimplencia
UNION ALL SELECT 'fraudes',              COUNT(*) FROM bronze.fraudes
UNION ALL SELECT 'ipca',                 COUNT(*) FROM bronze.ipca
UNION ALL SELECT 'selic',                COUNT(*) FROM bronze.selic
UNION ALL SELECT 'municipios',           COUNT(*) FROM bronze.municipios
ORDER BY tabela;
