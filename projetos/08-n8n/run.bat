@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo  BanVic 360 — Projeto 8: n8n
echo ============================================================
echo.

REM 1. Copiar .env.example se nao existir
if not exist .env (
    copy .env.example .env > nul
    echo [OK] .env criado a partir de .env.example
) else (
    echo [OK] .env ja existe
)

REM 2. Build + start dos containers
echo.
echo Subindo containers (n8n + PostgreSQL)...
docker compose up -d --build

if %errorlevel% neq 0 (
    echo [!!] Erro ao subir containers. Verifique o Docker.
    pause
    exit /b 1
)

REM 3. Aguardar n8n inicializar
echo.
echo Aguardando n8n inicializar (30s)...
timeout /t 30 /nobreak > nul

REM 4. Verificar se n8n esta respondendo
echo Verificando n8n em http://localhost:5678 ...
curl -s -o nul -w "%%{http_code}" http://localhost:5678 | findstr "200 301 302" > nul
if %errorlevel% equ 0 (
    echo [OK] n8n no ar!
) else (
    echo [!!] n8n ainda nao respondeu. Tente acessar http://localhost:5678 manualmente.
)

REM 5. Instrucoes finais
echo.
echo ============================================================
echo  PROXIMOS PASSOS:
echo ============================================================
echo.
echo  1. Acesse http://localhost:5678
echo     Login: admin / banvic2024
echo.
echo  2. Importe os workflows em Settings ^> Import:
echo     - workflows\01_pipeline_banvic.json
echo     - workflows\02_validar_kpis.json
echo.
echo  3. Configure a credencial PostgreSQL:
echo     Settings ^> Credentials ^> New ^> PostgreSQL
echo     Host: postgres  Port: 5432
echo     User: banvic_user  Pass: banvic_pass  DB: banvic
echo     Nome: BanVic PostgreSQL
echo.
echo  4. Carregue os dados Bronze (se ainda nao fez):
echo     docker exec banvic_n8n python3 /data/banvic/scripts/carga_bronze.py
echo.
echo  5. Execute o workflow "BanVic 360 - Pipeline ETL Completo"
echo.
echo ============================================================
echo.
pause
