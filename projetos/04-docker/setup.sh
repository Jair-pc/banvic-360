#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== BanVic 04 - Setup completo ==="
echo ""

cd "$SCRIPT_DIR"

echo "[1/6] Iniciando containers (postgres + pgadmin)..."
docker compose up -d

echo "[2/6] Aguardando banco ficar pronto..."
until docker compose exec -T postgres pg_isready -U banvic_user -d banvic > /dev/null 2>&1; do
    printf '.'
    sleep 2
done
echo " banco pronto"

echo "[3/6] Criando DDL Bronze..."
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /sql/01_bronze/ddl_bronze.sql

echo "[4/6] Carregando dados Bronze (~3.7M linhas, pode demorar 3-5 min)..."
cd "$PROJECT_ROOT"
PG_HOST=localhost PG_PORT=5433 python scripts/carga_bronze.py

echo "[5/6] Transformando Silver e populando Gold..."
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T postgres \
    psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic \
    -c "DROP SCHEMA IF EXISTS silver CASCADE; CREATE SCHEMA silver; DROP SCHEMA IF EXISTS gold CASCADE; CREATE SCHEMA gold;"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /sql/02_silver/ddl_silver_transforms.sql
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /sql/03_gold/ddl_modelo_dimensional.sql
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /proj01sql/01_populate_dims.sql
docker compose -f "$SCRIPT_DIR/docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /proj01sql/02_populate_fatos.sql

echo "[6/6] Validando 7 KPIs contra gabarito..."
PG_HOST=localhost PG_PORT=5433 python scripts/validar_gabarito_pg.py

echo ""
echo "Setup concluido!"
echo "  pgAdmin : http://localhost:5051  (admin@banvic.com / admin)"
echo "  Postgres: localhost:5433         (banvic_user / banvic_pass)"
