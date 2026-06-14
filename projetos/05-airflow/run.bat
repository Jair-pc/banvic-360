@echo off
echo =====================================================
echo  BanVic 360 - Projeto 5: Airflow
echo =====================================================

echo.
echo [PRE] Verificando banvic-base-postgres...
docker ps --filter "name=banvic-base-postgres" --filter "status=running" --format "{{.Names}}" | findstr banvic-base-postgres >nul
if errorlevel 1 (
    echo [ERRO] banvic-base-postgres nao esta rodando.
    echo        Execute na raiz do projeto:
    echo          docker compose up -d
    echo          python scripts/carga_bronze.py
    exit /b 1
)
echo [OK] banvic-base-postgres detectado.

echo.
echo [1/2] Inicializando banco de metadados do Airflow (primeira vez)...
docker compose up --abort-on-container-exit --exit-code-from airflow-init airflow-init
if errorlevel 1 (
    echo [ERRO] Inicializacao do Airflow falhou.
    exit /b 1
)

echo.
echo [2/2] Subindo Airflow (webserver + scheduler)...
docker compose up -d airflow-webserver airflow-scheduler
if errorlevel 1 (
    echo [ERRO] Falha ao subir webserver/scheduler.
    exit /b 1
)

echo.
echo [OK] Airflow disponivel em http://localhost:8080
echo      Login: admin / admin
echo.
echo      Para acionar a DAG manualmente:
echo        Abra o Airflow UI, ative a DAG "banvic_pipeline" e clique em Trigger.
echo.
echo      Para acompanhar os logs:
echo        docker logs -f banvic-p05-scheduler
echo =====================================================
