#!/usr/bin/env bash
set -euo pipefail

echo "====================================================="
echo " BanVic 360 - Projeto 3: Apache Hop"
echo "====================================================="

echo ""
echo "[PRE] Verificando se banvic-base-postgres esta rodando..."
if ! docker ps --filter "name=banvic-base-postgres" --filter "status=running" --format "{{.Names}}" | grep -q banvic-base-postgres; then
    echo "[ERRO] banvic-base-postgres nao esta rodando."
    echo "       Execute primeiro na raiz do projeto:"
    echo "         docker compose up -d"
    echo "         python scripts/carga_bronze.py"
    exit 1
fi
echo "[OK] banvic-base-postgres detectado."

echo ""
echo "[1/1] Executando workflow Apache Hop..."
docker compose up --abort-on-container-exit --exit-code-from hop

echo ""
echo "[OK] Pipeline concluido com sucesso!"
echo "     Execute para validar os KPIs:"
echo "       python scripts/validar_gabarito_pg.py"
echo "====================================================="
