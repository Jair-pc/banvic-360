#!/usr/bin/env bash
set -euo pipefail

echo "====================================================="
echo " BanVic 360 - Projeto 3: Apache Hop"
echo "====================================================="

echo ""
echo "[PRE] Verificando se banvic_postgres esta rodando..."
if ! docker ps --filter "name=banvic_postgres" --filter "status=running" --format "{{.Names}}" | grep -q banvic_postgres; then
    echo "[ERRO] banvic_postgres nao esta rodando."
    echo "       Execute primeiro na raiz do projeto:"
    echo "         docker compose up -d"
    echo "         python scripts/carga_bronze.py"
    exit 1
fi
echo "[OK] banvic_postgres detectado."

echo ""
echo "[1/1] Executando workflow Apache Hop..."
docker compose up --abort-on-container-exit --exit-code-from hop

echo ""
echo "[OK] Pipeline concluido com sucesso!"
echo "     Execute para validar os KPIs:"
echo "       python scripts/validar_gabarito_pg.py"
echo "====================================================="
