@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

echo === BanVic 04 - Setup completo ===
echo.

cd /d "%SCRIPT_DIR%"

echo [1/6] Iniciando containers (postgres + pgadmin)...
docker compose up -d
if %errorlevel% neq 0 (
    echo ERRO: docker compose up falhou
    exit /b 1
)

echo [2/6] Aguardando banco ficar pronto...
:WAIT
docker compose exec -T postgres pg_isready -U banvic_user -d banvic >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto WAIT
)
echo    banco pronto

echo [3/6] Criando DDL Bronze...
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /sql/01_bronze/ddl_bronze.sql
if %errorlevel% neq 0 (
    echo ERRO: DDL Bronze falhou
    exit /b 1
)

echo [4/6] Carregando dados Bronze (~3.7M linhas, pode demorar 3-5 min)...
cd /d "%PROJECT_ROOT%"
set PG_HOST=localhost
set PG_PORT=5433
python scripts/carga_bronze.py
if %errorlevel% neq 0 (
    echo ERRO: carga_bronze.py falhou
    exit /b 1
)

echo [5/6] Transformando Silver e populando Gold...
docker compose -f "%SCRIPT_DIR%docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /sql/02_silver/ddl_silver_transforms.sql
if %errorlevel% neq 0 (
    echo ERRO: transformacao Silver falhou
    exit /b 1
)
docker compose -f "%SCRIPT_DIR%docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /sql/03_gold/ddl_modelo_dimensional.sql
if %errorlevel% neq 0 (
    echo ERRO: DDL Gold falhou
    exit /b 1
)
docker compose -f "%SCRIPT_DIR%docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /proj01sql/01_populate_dims.sql
if %errorlevel% neq 0 (
    echo ERRO: carga das dimensoes Gold falhou
    exit /b 1
)
docker compose -f "%SCRIPT_DIR%docker-compose.yml" exec -T postgres psql -v ON_ERROR_STOP=1 -U banvic_user -d banvic -f /proj01sql/02_populate_fatos.sql
if %errorlevel% neq 0 (
    echo ERRO: carga dos fatos Gold falhou
    exit /b 1
)

echo [6/6] Validando 7 KPIs contra gabarito...
set PG_HOST=localhost
set PG_PORT=5433
python scripts/validar_gabarito_pg.py
if %errorlevel% neq 0 (
    echo ERRO: validacao dos KPIs falhou
    exit /b 1
)

echo.
echo Setup concluido!
echo   pgAdmin : http://localhost:5051  (admin@banvic.com / admin)
echo   Postgres: localhost:5433         (banvic_user / banvic_pass)

cd /d "%SCRIPT_DIR%"
endlocal
