-- ================================================================
-- BanVic 360 -- Setup: Schemas, Extensoes e Configuracoes
-- ================================================================
-- Executar UMA VEZ como superusuario antes de qualquer outro script.
-- PostgreSQL 14+
-- ================================================================

-- Extensoes
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- busca textual fuzzy
CREATE EXTENSION IF NOT EXISTS "btree_gin";   -- indices GIN em tipos basicos
CREATE EXTENSION IF NOT EXISTS "tablefunc";   -- crosstab / pivot

-- Schemas da arquitetura Lakehouse
CREATE SCHEMA IF NOT EXISTS bronze;    -- dados brutos sem transformacao
CREATE SCHEMA IF NOT EXISTS silver;    -- limpos, tipados, padronizados
CREATE SCHEMA IF NOT EXISTS gold;      -- modelo dimensional (star schema)
CREATE SCHEMA IF NOT EXISTS dq;        -- data quality / auditoria
CREATE SCHEMA IF NOT EXISTS staging;   -- area temporaria de carga incremental

COMMENT ON SCHEMA bronze  IS 'Camada Bronze: dados brutos ingeridos das fontes sem transformacao';
COMMENT ON SCHEMA silver  IS 'Camada Silver: dados limpos, tipados, padronizados e enriquecidos';
COMMENT ON SCHEMA gold    IS 'Camada Gold: modelo dimensional Star Schema para analytics';
COMMENT ON SCHEMA dq      IS 'Data Quality: log de auditorias e regras de qualidade';
COMMENT ON SCHEMA staging IS 'Area temporaria para carga incremental e reconciliacao';
