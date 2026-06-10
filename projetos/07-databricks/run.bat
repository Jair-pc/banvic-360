@echo off
echo =====================================================
echo  BanVic 360 - Projeto 7: Databricks Lakehouse
echo =====================================================
echo.

REM Verificar Databricks CLI
where databricks >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Databricks CLI nao encontrada.
    echo        pip install databricks-cli
    echo        databricks configure --token
    exit /b 1
)

echo [1/3] Criando pastas no workspace...
databricks workspace mkdirs /Workspace/banvic-360/projetos/07-databricks/notebooks
databricks workspace mkdirs /Workspace/banvic-360/projetos/07-databricks/dlt

echo.
echo [2/3] Importando notebooks...
for %%N in (00_setup 01_bronze 02_silver 03_gold_dims 04_gold_fatos 05_validar_kpis) do (
    databricks workspace import --language PYTHON --overwrite ^
        notebooks\%%N.py ^
        /Workspace/banvic-360/projetos/07-databricks/notebooks/%%N
    if errorlevel 1 (
        echo [ERRO] Falha ao importar %%N
        exit /b 1
    )
    echo   OK  %%N
)

databricks workspace import --language PYTHON --overwrite ^
    dlt\banvic_pipeline_dlt.py ^
    /Workspace/banvic-360/projetos/07-databricks/dlt/banvic_pipeline_dlt
echo   OK  banvic_pipeline_dlt

echo.
echo [3/3] Criando job...
databricks jobs create --json @job_config.json

echo.
echo [OK] Notebooks importados com sucesso!
echo      Acesse a UI: Engenharia de Dados - Corridas
echo =====================================================
