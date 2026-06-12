-- Schemas e extensoes criados automaticamente no primeiro start do container
-- Executado via /docker-entrypoint-initdb.d antes de qualquer dado ser carregado

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "tablefunc";

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS dq;
CREATE SCHEMA IF NOT EXISTS staging;

COMMENT ON SCHEMA bronze  IS 'Camada Bronze: dados brutos ingeridos sem transformacao';
COMMENT ON SCHEMA silver  IS 'Camada Silver: dados limpos, tipados e padronizados';
COMMENT ON SCHEMA gold    IS 'Camada Gold: modelo dimensional Star Schema para analytics';
