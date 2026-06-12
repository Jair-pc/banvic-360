"""
Testa os callables do DAG banvic_pipeline diretamente via psycopg2,
sem precisar do Airflow rodando. Prova que o SQL funciona corretamente.
"""
import json
import logging
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
GABARITO_PATH = ROOT / "docs/gabarito/gabarito.json"

PG_CONN = dict(host="localhost", port=5432, dbname="banvic",
               user="banvic_user", password="banvic_pass")

# --- Silver SQL (do DAG) ---

SILVER_SQL_CLIENTES = """
DROP TABLE IF EXISTS silver.clientes_clean CASCADE;
CREATE TABLE silver.clientes_clean AS
SELECT
    cod_cliente::INTEGER                                                        AS cod_cliente,
    TRIM(primeiro_nome)                                                         AS primeiro_nome,
    TRIM(ultimo_nome)                                                           AS ultimo_nome,
    LOWER(TRIM(email))                                                          AS email,
    UPPER(TRIM(tipo_cliente))                                                   AS tipo_pessoa,
    data_inclusao::DATE                                                         AS data_inclusao,
    REGEXP_REPLACE(cpfcnpj, '[^0-9]', '', 'g')                                 AS cpf_digits,
    cpfcnpj                                                                     AS cpf_formatado,
    data_nascimento::DATE                                                       AS data_nascimento,
    EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE))::SMALLINT AS idade,
    CASE
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 18 AND 24 THEN '18-24'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 25 AND 34 THEN '25-34'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 35 AND 44 THEN '35-44'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 45 AND 54 THEN '45-54'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) BETWEEN 55 AND 64 THEN '55-64'
        WHEN EXTRACT(YEAR FROM AGE('2026-06-10'::DATE, data_nascimento::DATE)) >= 65              THEN '65+'
        ELSE 'Menor'
    END                                                                         AS faixa_etaria,
    TRIM(endereco)                                                              AS endereco,
    REGEXP_REPLACE(cep, '[^0-9]', '', 'g')                                     AS cep_digits,
    NOW()                                                                       AS _silver_ts
FROM bronze.clientes
WHERE cod_cliente IS NOT NULL AND cpfcnpj IS NOT NULL;

DROP TABLE IF EXISTS silver.clientes_sinteticos_clean CASCADE;
CREATE TABLE silver.clientes_sinteticos_clean AS
SELECT
    cod_cliente::INTEGER        AS cod_cliente,
    TRIM(primeiro_nome)         AS primeiro_nome,
    TRIM(ultimo_nome)           AS ultimo_nome,
    LOWER(TRIM(email))          AS email,
    UPPER(tipo_cliente)         AS tipo_pessoa,
    data_inclusao::DATE         AS data_inclusao,
    cpfcnpj                     AS cpf_formatado,
    data_nascimento::DATE       AS data_nascimento,
    idade::SMALLINT             AS idade,
    faixa_etaria, cidade,
    UPPER(uf) AS uf, cep,
    renda_mensal::NUMERIC(12,2) AS renda_mensal,
    faixa_renda, profissao, escolaridade,
    score_credito::SMALLINT     AS score_credito,
    faixa_score,
    NOW()                       AS _silver_ts
FROM bronze.clientes_sinteticos
WHERE cod_cliente IS NOT NULL;
"""


def run_sql(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def test_preparar_ambiente(conn):
    log.info("[preparar_ambiente] dropping Silver + truncating Gold dims/fatos...")
    sql = """
        DROP TABLE IF EXISTS silver.clientes_clean              CASCADE;
        DROP TABLE IF EXISTS silver.clientes_sinteticos_clean   CASCADE;
        DROP TABLE IF EXISTS silver.contas_clean                CASCADE;
        DROP TABLE IF EXISTS silver.transacoes_clean            CASCADE;
        DROP TABLE IF EXISTS silver.agencias_clean              CASCADE;
        DROP TABLE IF EXISTS silver.colaboradores_clean         CASCADE;
        DROP TABLE IF EXISTS silver.propostas_clean             CASCADE;
        DROP TABLE IF EXISTS silver.ipca_clean                  CASCADE;
        DROP TABLE IF EXISTS silver.selic_clean                 CASCADE;
        DROP TABLE IF EXISTS silver.municipios_clean            CASCADE;
        TRUNCATE gold.fato_transacoes          CASCADE;
        TRUNCATE gold.fato_contas              CASCADE;
        TRUNCATE gold.fato_propostas_credito   CASCADE;
        TRUNCATE gold.dim_cliente              CASCADE;
        TRUNCATE gold.dim_agencia              CASCADE;
        TRUNCATE gold.dim_colaborador          CASCADE;
        TRUNCATE gold.dim_municipio            CASCADE;
        TRUNCATE gold.dim_canal                CASCADE;
    """
    run_sql(conn, sql)
    log.info("[preparar_ambiente] OK")


def test_silver_clientes(conn):
    log.info("[silver/clientes] rebuilding clientes_clean + clientes_sinteticos_clean...")
    run_sql(conn, SILVER_SQL_CLIENTES)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM silver.clientes_clean")
        n = cur.fetchone()[0]
    log.info("[silver/clientes] clientes_clean: %d rows", n)
    assert n == 998, f"Expected 998, got {n}"


def test_silver_externos(conn):
    log.info("[silver/externos] rebuilding ipca_clean, selic_clean, municipios_clean...")
    sql = (ROOT / "sql/02_silver/ddl_silver_transforms.sql").read_text()
    # run only the externos portion via direct SQL
    ext_sql = """
        DROP TABLE IF EXISTS silver.ipca_clean CASCADE;
        CREATE TABLE silver.ipca_clean AS
        SELECT data::DATE, ano::SMALLINT, mes, mes_num::SMALLINT,
               indice::NUMERIC(10,2), no_mes::NUMERIC(6,2),
               acumulado_12m::NUMERIC(6,2), acumulado_ano::NUMERIC(6,2),
               'REAL' AS tipo, NOW() AS _silver_ts
        FROM bronze.ipca WHERE data ~ '^\\d{4}-\\d{2}-\\d{2}$'
        UNION ALL
        SELECT data::DATE, ano::SMALLINT, mes, mes_num::SMALLINT,
               indice::NUMERIC(10,2), no_mes::NUMERIC(6,2),
               acumulado_12m::NUMERIC(6,2), acumulado_ano::NUMERIC(6,2),
               tipo, NOW()
        FROM bronze.ipca_projetado WHERE tipo = 'PROJECAO';

        DROP TABLE IF EXISTS silver.selic_clean CASCADE;
        CREATE TABLE silver.selic_clean AS
        SELECT data::DATE,
               taxa_selic::NUMERIC(10,6)       AS taxa_selic,
               taxa_selic::NUMERIC * 252 * 100 AS taxa_selic_aa,
               'REAL' AS tipo, NOW() AS _silver_ts
        FROM bronze.selic
        UNION ALL
        SELECT data::DATE, taxa_selic::NUMERIC(10,6),
               taxa_selic::NUMERIC * 252 * 100, tipo, NOW()
        FROM bronze.selic_projetada WHERE tipo = 'PROJECAO';

        DROP TABLE IF EXISTS silver.municipios_clean CASCADE;
        CREATE TABLE silver.municipios_clean AS
        SELECT m.codigo_ibge::INTEGER AS codigo_ibge, m.municipio,
               UPPER(m.uf) AS uf, 'Sudeste' AS regiao,
               p.populacao::INTEGER AS populacao, p.ano::SMALLINT AS ano_populacao,
               pib.pib_total::BIGINT AS pib_total,
               pib.pib_per_capita::NUMERIC AS pib_per_capita,
               pib.ano::SMALLINT AS ano_pib, NOW() AS _silver_ts
        FROM bronze.municipios m
        LEFT JOIN bronze.populacao p ON p.codigo_ibge = m.codigo_ibge AND p.ano = '2022'
        LEFT JOIN bronze.pib_municipal pib ON pib.codigo_ibge = m.codigo_ibge AND pib.ano = '2021'
        WHERE m.codigo_ibge IS NOT NULL;
    """
    run_sql(conn, ext_sql)
    log.info("[silver/externos] OK")


def test_gold_dims(conn):
    log.info("[gold/dims] populating Gold dimensions...")
    sql = (ROOT / "projetos/01-sql-puro/sql/01_populate_dims.sql").read_text()
    run_sql(conn, sql)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM gold.dim_cliente WHERE eh_registro_atual = TRUE")
        n = cur.fetchone()[0]
    log.info("[gold/dims] dim_cliente: %d rows", n)
    assert n > 0, "dim_cliente is empty"


def test_gold_fatos(conn):
    log.info("[gold/fatos] populating Gold facts...")
    sql = (ROOT / "projetos/01-sql-puro/sql/02_populate_fatos.sql").read_text()
    run_sql(conn, sql)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM gold.fato_transacoes")
        n = cur.fetchone()[0]
    log.info("[gold/fatos] fato_transacoes: %d rows", n)
    assert n > 0, "fato_transacoes is empty"


def test_validar_kpis(_conn):
    """Delega para validar_gabarito_pg.py — script canonico que trata encoding corretamente."""
    import subprocess
    log.info("[validar_kpis] delegando para validar_gabarito_pg.py...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validar_gabarito_pg.py")],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        log.error("REPROVADO: validar_gabarito_pg.py retornou exit code %d", result.returncode)
        return False
    log.info("APROVADO: todos os 8 KPIs OK (via validar_gabarito_pg.py)")
    return True


if __name__ == "__main__":
    log.info("Conectando ao PostgreSQL...")
    conn = psycopg2.connect(**PG_CONN)  # sem forcar UTF8 — gabarito.json usa a mesma codificacao
    conn.autocommit = False

    try:
        test_preparar_ambiente(conn)
        test_silver_clientes(conn)    # rebuild clientes_clean (com data fixa)
        # rebuild demais tabelas Silver usando o DDL principal
        log.info("[silver/restante] rebuilding contas, transacoes, agencias, colaboradores, propostas, externos...")
        silver_ddl = (ROOT / "sql/02_silver/ddl_silver_transforms.sql").read_text()
        run_sql(conn, silver_ddl)
        log.info("[silver/restante] OK")
        test_gold_dims(conn)
        test_gold_fatos(conn)
        ok = test_validar_kpis(conn)
        sys.exit(0 if ok else 1)
    except Exception as e:
        log.error("ERRO: %s", e)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()
