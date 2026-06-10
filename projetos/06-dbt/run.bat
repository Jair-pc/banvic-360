@echo off
echo =====================================================
echo  BanVic 360 - Projeto 6: dbt
echo =====================================================

echo.
echo [PRE] Verificando banvic_postgres...
docker ps --filter "name=banvic_postgres" --filter "status=running" --format "{{.Names}}" | findstr banvic_postgres >nul
if errorlevel 1 (
    echo [ERRO] banvic_postgres nao esta rodando.
    echo        Execute na raiz do projeto:
    echo          docker compose up -d
    echo          python scripts/carga_bronze.py
    exit /b 1
)
echo [OK] banvic_postgres detectado.

echo.
echo [1/2] dbt run (Bronze -> Silver -> Gold)...
docker compose run --rm dbt run --profiles-dir /banvic_dbt
if errorlevel 1 (
    echo [ERRO] dbt run falhou. Verifique os logs acima.
    exit /b 1
)

echo.
echo [2/2] dbt test (testes de qualidade + validacao KPIs)...
docker compose run --rm dbt test --profiles-dir /banvic_dbt

echo.
echo [OK] Pipeline dbt concluido com sucesso!
echo      Para gerar e visualizar a documentacao:
echo        docker compose run --rm dbt docs generate --profiles-dir /banvic_dbt
echo        docker compose run --rm -p 8081:8080 dbt docs serve
echo =====================================================
