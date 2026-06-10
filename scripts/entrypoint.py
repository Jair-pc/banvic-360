"""
BanVic 360 -- Pipeline completo
================================
Executa em sequencia: Setup -> Bronze -> Silver -> Gold -> Validacao

Uso:
    python scripts/entrypoint.py
    python scripts/entrypoint.py --skip-setup
    python scripts/entrypoint.py --only gold
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

ROOT = Path(__file__).parent.parent
SQL  = ROOT / "sql"

PG_CONN = {
    "host":     os.getenv("PG_HOST", "localhost"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB", "banvic"),
    "user":     os.getenv("PG_USER", "banvic_user"),
    "password": os.getenv("PG_PASSWORD", "banvic_pass"),
}


# ─── Utilitarios ─────────────────────────────────────────────────────────────

def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def conectar() -> psycopg2.extensions.connection:
    return psycopg2.connect(**PG_CONN)


def aguardar_postgres(tentativas: int = 10, intervalo: int = 3):
    log("Aguardando PostgreSQL...")
    for i in range(tentativas):
        try:
            conn = conectar()
            conn.close()
            log("PostgreSQL disponivel.")
            return
        except psycopg2.OperationalError:
            log(f"  Tentativa {i+1}/{tentativas}. Aguardando {intervalo}s...")
            time.sleep(intervalo)
    print("ERRO: PostgreSQL nao respondeu. Verifique se o banco esta rodando.")
    sys.exit(1)


def executar_sql(conn, caminho: Path, descricao: str):
    log(f"Executando: {descricao}")
    sql = caminho.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    log(f"  OK: {descricao}")


def executar_script(caminho: Path, descricao: str, args: list[str] | None = None):
    log(f"Executando: {descricao}")
    cmd = [sys.executable, str(caminho)] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERRO em {descricao}:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(1)
    if result.stdout:
        for linha in result.stdout.strip().splitlines():
            print(f"    {linha}")
    log(f"  OK: {descricao}")


# ─── Etapas ──────────────────────────────────────────────────────────────────

def etapa_setup(conn):
    log("=== SETUP: Schemas e extensoes ===")
    executar_sql(conn, SQL / "00_setup" / "00_schemas_extensoes.sql", "schemas + extensoes")


def etapa_bronze(conn):
    log("=== BRONZE: Carga bruta ===")
    executar_sql(conn, SQL / "01_bronze" / "ddl_bronze.sql", "DDL bronze")
    # carga_bronze usa COPY com caminhos; usa script Python se disponivel
    carga_py = ROOT / "scripts" / "carga_bronze.py"
    carga_sql = SQL / "01_bronze" / "carga_bronze.sql"
    if carga_py.exists():
        executar_script(carga_py, "carga bronze (Python)")
    elif carga_sql.exists():
        executar_sql(conn, carga_sql, "carga bronze (SQL COPY)")
    else:
        log("  AVISO: nenhum loader bronze encontrado. Pule ou crie scripts/carga_bronze.py")


def etapa_silver(conn):
    log("=== SILVER: Transformacoes e Data Quality ===")
    executar_sql(conn, SQL / "02_silver" / "data_quality_framework.sql", "DQ framework")
    executar_sql(conn, SQL / "02_silver" / "ddl_silver_transforms.sql", "transforms Silver")


def etapa_gold(conn):
    log("=== GOLD: Modelo dimensional ===")
    executar_sql(conn, SQL / "03_gold" / "ddl_modelo_dimensional.sql", "DDL Gold + KPI views")


def etapa_validacao():
    log("=== VALIDACAO: Comparando KPIs com gabarito ===")
    validador_pg = ROOT / "scripts" / "validar_gabarito_pg.py"
    validador_csv = ROOT / "scripts" / "validar_gabarito.py"

    if validador_pg.exists():
        executar_script(validador_pg, "validacao PostgreSQL vs gabarito")
    elif validador_csv.exists():
        executar_script(validador_csv, "recalculo gabarito (CSV)")
        log("  AVISO: validacao apenas dos CSVs. Use validar_gabarito_pg.py para comparar com PostgreSQL.")
    else:
        log("  AVISO: nenhum validador encontrado.")


# ─── Main ─────────────────────────────────────────────────────────────────────

ETAPAS = {
    "setup":    etapa_setup,
    "bronze":   etapa_bronze,
    "silver":   etapa_silver,
    "gold":     etapa_gold,
}


def main():
    parser = argparse.ArgumentParser(description="BanVic 360 -- Pipeline completo")
    parser.add_argument("--skip-setup", action="store_true",
                        help="Pular etapa de setup (schemas/extensoes)")
    parser.add_argument("--only", choices=list(ETAPAS.keys()),
                        help="Executar apenas uma etapa especifica")
    args = parser.parse_args()

    inicio = time.time()
    log("=== BanVic 360 -- Iniciando pipeline ===")

    aguardar_postgres()

    conn = conectar()
    try:
        if args.only:
            fn = ETAPAS[args.only]
            if fn.__code__.co_varnames[0] == "conn":
                fn(conn)
            else:
                fn()
        else:
            etapas = list(ETAPAS.items())
            if args.skip_setup:
                etapas = [(k, v) for k, v in etapas if k != "setup"]
            for _, fn in etapas:
                fn(conn)
            etapa_validacao()
    finally:
        conn.close()

    duracao = time.time() - inicio
    log(f"=== Pipeline concluido em {duracao:.1f}s ===")


if __name__ == "__main__":
    main()
