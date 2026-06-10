#!/usr/bin/env bash
# BanVic 360 — Projeto 7: Databricks
# Usa Databricks CLI para importar notebooks e disparar o pipeline.
# Requer: pip install databricks-cli && databricks configure --token

set -euo pipefail

echo "====================================================="
echo " BanVic 360 - Projeto 7: Databricks Lakehouse"
echo "====================================================="
echo ""

# Verificar CLI instalada
if ! command -v databricks &> /dev/null; then
    echo "[ERRO] Databricks CLI nao encontrada."
    echo "       pip install databricks-cli"
    echo "       databricks configure --token"
    exit 1
fi

echo "[1/3] Criando pasta no workspace..."
databricks workspace mkdirs /Workspace/banvic-360/projetos/07-databricks/notebooks
databricks workspace mkdirs /Workspace/banvic-360/projetos/07-databricks/dlt

echo ""
echo "[2/3] Importando notebooks..."
for nb in notebooks/00_setup notebooks/01_bronze notebooks/02_silver \
          notebooks/03_gold_dims notebooks/04_gold_fatos notebooks/05_validar_kpis; do
    databricks workspace import \
        --language PYTHON \
        --overwrite \
        "${nb}.py" \
        "/Workspace/banvic-360/projetos/07-databricks/${nb}"
    echo "  OK  ${nb}"
done

databricks workspace import \
    --language PYTHON --overwrite \
    dlt/banvic_pipeline_dlt.py \
    /Workspace/banvic-360/projetos/07-databricks/dlt/banvic_pipeline_dlt

echo ""
echo "[3/3] Criando/atualizando job..."
JOB_ID=$(databricks jobs create --json @job_config.json | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "  Job ID: ${JOB_ID}"

echo ""
echo "[OK] Notebooks importados. Para executar:"
echo "     databricks jobs run-now --job-id ${JOB_ID}"
echo ""
echo "     Ou acesse a UI: Engenharia de Dados -> Corridas"
echo "====================================================="
