"""
BanVic 360 — DAG principal
Bronze -> Silver -> Gold -> Validacao KPIs

Schedule: diario as 06:00
Retries: 2 tentativas com 3 min de intervalo entre elas
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

log = logging.getLogger(__name__)

CONN_ID       = "banvic_pg"
BANVIC_ROOT   = Path("/opt/banvic")
GABARITO_PATH = BANVIC_ROOT / "docs/gabarito/gabarito.json"

# ── SQL Silver por entidade ───────────────────────────────────────────────────
# Cada bloco e idempotente: DROP + CREATE TABLE AS SELECT
# Os tasks Silver rodam em paralelo — cada um e responsavel pela propria tabela.

SILVER_SQL: dict[str, str] = {

    "clientes": """
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
            cod_cliente::INTEGER          AS cod_cliente,
            TRIM(primeiro_nome)           AS primeiro_nome,
            TRIM(ultimo_nome)             AS ultimo_nome,
            LOWER(TRIM(email))            AS email,
            UPPER(tipo_cliente)           AS tipo_pessoa,
            data_inclusao::DATE           AS data_inclusao,
            cpfcnpj                       AS cpf_formatado,
            data_nascimento::DATE         AS data_nascimento,
            idade::SMALLINT               AS idade,
            faixa_etaria,
            cidade,
            UPPER(uf)                     AS uf,
            cep,
            renda_mensal::NUMERIC(12,2)   AS renda_mensal,
            faixa_renda,
            profissao,
            escolaridade,
            score_credito::SMALLINT       AS score_credito,
            faixa_score,
            NOW()                         AS _silver_ts
        FROM bronze.clientes_sinteticos
        WHERE cod_cliente IS NOT NULL;
    """,

    "contas": """
        DROP TABLE IF EXISTS silver.contas_clean CASCADE;
        CREATE TABLE silver.contas_clean AS
        SELECT
            num_conta::INTEGER            AS num_conta,
            cod_cliente::INTEGER          AS cod_cliente,
            cod_agencia::INTEGER          AS cod_agencia,
            cod_colaborador::INTEGER      AS cod_colaborador,
            TRIM(tipo_conta)              AS tipo_conta,
            data_abertura::DATE           AS data_abertura,
            ROUND(saldo_total::NUMERIC, 2)      AS saldo_total,
            ROUND(saldo_disponivel::NUMERIC, 2) AS saldo_disponivel,
            data_ultimo_lancamento::DATE        AS data_ultimo_lancamento,
            CASE WHEN data_ultimo_lancamento::DATE >=
                      (SELECT MAX(data_ultimo_lancamento::DATE) FROM bronze.contas) - 90
                 THEN TRUE ELSE FALSE END       AS eh_conta_ativa,
            NOW()                               AS _silver_ts
        FROM bronze.contas
        WHERE num_conta IS NOT NULL
          AND saldo_total ~ '^-?[0-9]+\\.?[0-9]*$';
    """,

    "transacoes": """
        DROP TABLE IF EXISTS silver.transacoes_clean CASCADE;
        CREATE TABLE silver.transacoes_clean AS
        SELECT
            cod_transacao::INTEGER          AS cod_transacao,
            num_conta::INTEGER              AS num_conta,
            data_transacao::TIMESTAMP       AS data_transacao,
            DATE_TRUNC('month', data_transacao::TIMESTAMP)::DATE AS mes_referencia,
            TRIM(nome_transacao)            AS nome_transacao,
            valor_transacao::NUMERIC(14,2)  AS valor_transacao,
            ABS(valor_transacao::NUMERIC)   AS valor_absoluto,
            CASE WHEN valor_transacao::NUMERIC >= 0 THEN TRUE ELSE FALSE END AS flag_credito,
            CASE
                WHEN nome_transacao ILIKE '%pix%'      THEN 'Pix'
                WHEN nome_transacao ILIKE '%ted%'      THEN 'TED'
                WHEN nome_transacao ILIKE '%doc%'      THEN 'DOC'
                WHEN nome_transacao ILIKE '%credito%'  THEN 'Compra Credito'
                WHEN nome_transacao ILIKE '%debito%'   THEN 'Compra Debito'
                WHEN nome_transacao ILIKE '%saque%'    THEN 'Saque'
                WHEN nome_transacao ILIKE '%deposito%' THEN 'Deposito Especie'
                WHEN nome_transacao ILIKE '%boleto%'   THEN 'Pagamento Boleto'
                ELSE 'Outros'
            END                             AS canal,
            NOW()                           AS _silver_ts
        FROM bronze.transacoes
        WHERE cod_transacao IS NOT NULL
          AND valor_transacao ~ '^-?[0-9]+\\.?[0-9]*$'
          AND valor_transacao::NUMERIC <> 0;
    """,

    "agencias": """
        DROP TABLE IF EXISTS silver.agencias_clean CASCADE;
        CREATE TABLE silver.agencias_clean AS
        SELECT
            a.cod_agencia::INTEGER          AS cod_agencia,
            TRIM(a.nome)                    AS nome,
            UPPER(TRIM(a.tipo_agencia))     AS tipo_agencia,
            a.cidade,
            UPPER(a.uf)                     AS uf,
            CASE UPPER(a.uf)
                WHEN 'SP' THEN 'Sudeste' WHEN 'RJ' THEN 'Sudeste'
                WHEN 'MG' THEN 'Sudeste' WHEN 'ES' THEN 'Sudeste'
                WHEN 'RS' THEN 'Sul'     WHEN 'SC' THEN 'Sul'     WHEN 'PR' THEN 'Sul'
                WHEN 'BA' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
                WHEN 'CE' THEN 'Nordeste' WHEN 'MA' THEN 'Nordeste'
                WHEN 'PB' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste'
                WHEN 'AL' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste' WHEN 'PI' THEN 'Nordeste'
                WHEN 'GO' THEN 'Centro-Oeste' WHEN 'MT' THEN 'Centro-Oeste'
                WHEN 'MS' THEN 'Centro-Oeste' WHEN 'DF' THEN 'Centro-Oeste'
                WHEN 'AM' THEN 'Norte' WHEN 'PA' THEN 'Norte' WHEN 'AC' THEN 'Norte'
                WHEN 'RO' THEN 'Norte' WHEN 'RR' THEN 'Norte'
                WHEN 'AP' THEN 'Norte' WHEN 'TO' THEN 'Norte'
                ELSE 'Sudeste'
            END                             AS regiao,
            a.data_abertura::DATE           AS data_abertura,
            COALESCE(e.meta_comercial_mensal::NUMERIC, 500000) AS meta_comercial_mensal,
            COALESCE(e.latitude::NUMERIC, NULL)  AS latitude,
            COALESCE(e.longitude::NUMERIC, NULL) AS longitude,
            TRUE                            AS eh_ativa,
            NOW()                           AS _silver_ts
        FROM bronze.agencias a
        LEFT JOIN bronze.agencias_expandidas e ON e.cod_agencia = a.cod_agencia
        WHERE a.cod_agencia IS NOT NULL;
    """,

    "colaboradores": """
        DROP TABLE IF EXISTS silver.colaboradores_clean CASCADE;
        CREATE TABLE silver.colaboradores_clean AS
        SELECT
            e.cod_colaborador::INTEGER      AS cod_colaborador,
            e.primeiro_nome, e.ultimo_nome,
            LOWER(e.email)                  AS email,
            e.cpf,
            e.data_nascimento::DATE         AS data_nascimento,
            e.cidade, UPPER(e.uf) AS uf, e.regiao,
            e.cargo,
            e.nivel_hierarquico::SMALLINT   AS nivel_hierarquico,
            e.departamento,
            e.salario_base::NUMERIC(12,2)   AS salario_base,
            e.cod_agencia::INTEGER          AS cod_agencia,
            e.data_admissao::DATE           AS data_admissao,
            NULLIF(e.data_demissao, '')::DATE AS data_demissao,
            e.eh_ativo::BOOLEAN             AS eh_ativo,
            NOW()                           AS _silver_ts
        FROM bronze.colaboradores_expandidos e
        WHERE e.cod_colaborador IS NOT NULL

        UNION ALL

        SELECT
            c.cod_colaborador::INTEGER,
            c.primeiro_nome, c.ultimo_nome,
            LOWER(c.email), c.cpf,
            c.data_nascimento::DATE,
            NULL, NULL, NULL, c.cargo,
            NULL::SMALLINT, NULL, NULL::NUMERIC,
            NULL::INTEGER,
            NULL::DATE, NULL::DATE, TRUE, NOW()
        FROM bronze.colaboradores c
        WHERE NOT EXISTS (
            SELECT 1 FROM bronze.colaboradores_expandidos e
            WHERE e.cod_colaborador = c.cod_colaborador
        );
    """,

    "propostas": """
        DROP TABLE IF EXISTS silver.propostas_clean CASCADE;
        CREATE TABLE silver.propostas_clean AS
        SELECT
            cod_proposta::INTEGER               AS cod_proposta,
            cod_cliente::INTEGER                AS cod_cliente,
            cod_colaborador::INTEGER            AS cod_colaborador,
            data_entrada_proposta::DATE         AS data_entrada_proposta,
            taxa_juros_mensal::NUMERIC(8,6)     AS taxa_juros_mensal,
            valor_proposta::NUMERIC(14,2)       AS valor_proposta,
            valor_financiamento::NUMERIC(14,2)  AS valor_financiamento,
            valor_entrada::NUMERIC(14,2)        AS valor_entrada,
            valor_prestacao::NUMERIC(14,2)      AS valor_prestacao,
            quantidade_parcelas::SMALLINT       AS quantidade_parcelas,
            COALESCE(NULLIF(carencia,'')::SMALLINT, 0) AS carencia_dias,
            TRIM(status_proposta)               AS status_proposta,
            NOW()                               AS _silver_ts
        FROM bronze.propostas_credito
        WHERE cod_proposta IS NOT NULL
          AND valor_proposta ~ '^[0-9]+\\.?[0-9]*$'

        UNION ALL

        SELECT
            cod_proposta::INTEGER, cod_cliente::INTEGER,
            cod_colaborador::INTEGER,
            data_entrada_proposta::DATE,
            taxa_juros_mensal::NUMERIC(8,6),
            valor_proposta::NUMERIC(14,2),
            valor_financiamento::NUMERIC(14,2),
            valor_entrada::NUMERIC(14,2),
            valor_prestacao::NUMERIC(14,2),
            quantidade_parcelas::SMALLINT,
            COALESCE(NULLIF(carencia,'')::SMALLINT, 0),
            TRIM(status_proposta), NOW()
        FROM bronze.propostas_sinteticas
        WHERE cod_proposta IS NOT NULL;
    """,

    "externos": """
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
               taxa_selic::NUMERIC(10,6)           AS taxa_selic,
               taxa_selic::NUMERIC * 252 * 100     AS taxa_selic_aa,
               'REAL'                              AS tipo,
               NOW()                               AS _silver_ts
        FROM bronze.selic
        UNION ALL
        SELECT data::DATE,
               taxa_selic::NUMERIC(10,6),
               taxa_selic::NUMERIC * 252 * 100,
               tipo, NOW()
        FROM bronze.selic_projetada WHERE tipo = 'PROJECAO';

        DROP TABLE IF EXISTS silver.municipios_clean CASCADE;
        CREATE TABLE silver.municipios_clean AS
        SELECT m.codigo_ibge::INTEGER AS codigo_ibge,
               m.municipio,
               UPPER(m.uf) AS uf,
               CASE UPPER(m.uf)
                   WHEN 'SP' THEN 'Sudeste' WHEN 'RJ' THEN 'Sudeste'
                   WHEN 'MG' THEN 'Sudeste' WHEN 'ES' THEN 'Sudeste'
                   WHEN 'RS' THEN 'Sul'     WHEN 'SC' THEN 'Sul'   WHEN 'PR' THEN 'Sul'
                   WHEN 'BA' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
                   WHEN 'CE' THEN 'Nordeste' WHEN 'MA' THEN 'Nordeste'
                   WHEN 'PB' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste'
                   WHEN 'AL' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste'
                   WHEN 'PI' THEN 'Nordeste'
                   WHEN 'GO' THEN 'Centro-Oeste' WHEN 'MT' THEN 'Centro-Oeste'
                   WHEN 'MS' THEN 'Centro-Oeste' WHEN 'DF' THEN 'Centro-Oeste'
                   WHEN 'AM' THEN 'Norte' WHEN 'PA' THEN 'Norte'
                   WHEN 'AC' THEN 'Norte' WHEN 'RO' THEN 'Norte'
                   WHEN 'RR' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'TO' THEN 'Norte'
                   ELSE 'Sudeste'
               END AS regiao,
               p.populacao::INTEGER                AS populacao,
               p.ano::SMALLINT                     AS ano_populacao,
               pib.pib_total::BIGINT               AS pib_total,
               pib.pib_per_capita::NUMERIC         AS pib_per_capita,
               pib.ano::SMALLINT                   AS ano_pib,
               NOW()                               AS _silver_ts
        FROM bronze.municipios m
        LEFT JOIN bronze.populacao p
               ON p.codigo_ibge = m.codigo_ibge AND p.ano = '2022'
        LEFT JOIN bronze.pib_municipal pib
               ON pib.codigo_ibge = m.codigo_ibge AND pib.ano = '2021'
        WHERE m.codigo_ibge IS NOT NULL;
    """,

    "indices": """
        CREATE INDEX IF NOT EXISTS idx_sc_cod    ON silver.clientes_clean(cod_cliente);
        CREATE INDEX IF NOT EXISTS idx_sc_faixa  ON silver.clientes_clean(faixa_etaria);
        CREATE INDEX IF NOT EXISTS idx_cv_num    ON silver.contas_clean(num_conta);
        CREATE INDEX IF NOT EXISTS idx_cv_cli    ON silver.contas_clean(cod_cliente);
        CREATE INDEX IF NOT EXISTS idx_cv_ag     ON silver.contas_clean(cod_agencia);
        CREATE INDEX IF NOT EXISTS idx_tc_data   ON silver.transacoes_clean(data_transacao);
        CREATE INDEX IF NOT EXISTS idx_tc_mes    ON silver.transacoes_clean(mes_referencia);
        CREATE INDEX IF NOT EXISTS idx_tc_conta  ON silver.transacoes_clean(num_conta);
    """,
}

# ── helpers ───────────────────────────────────────────────────────────────────

def get_hook() -> PostgresHook:
    return PostgresHook(postgres_conn_id=CONN_ID)


# ── callables ─────────────────────────────────────────────────────────────────

def _check_bronze(**_) -> bool:
    count = get_hook().get_first("SELECT COUNT(*) FROM bronze.transacoes")[0]
    if count == 0:
        log.warning("Bronze vazio — execucao bloqueada. Execute carga_bronze.py primeiro.")
        return False
    log.info("Bronze OK: %d transacoes carregadas", count)
    return True


def _preparar_ambiente(**_):
    # dim_tempo NAO e truncada — e uma dimensao de referencia pre-populada pelo DDL
    # e apenas atualizada (UPDATE) com indicadores economicos, nao recriada a cada run.
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
    get_hook().run(sql)
    log.info("Silver dropped + Gold dims/fatos truncated (dim_tempo preservada)")


def _silver_task(entity: str, **_):
    get_hook().run(SILVER_SQL[entity])
    log.info("Silver %s: OK", entity)


def _gold_dims(**_):
    sql = (BANVIC_ROOT / "projetos/01-sql-puro/sql/01_populate_dims.sql").read_text()
    get_hook().run(sql)
    log.info("Gold dims: OK")


def _gold_fatos(**_):
    sql = (BANVIC_ROOT / "projetos/01-sql-puro/sql/02_populate_fatos.sql").read_text()
    get_hook().run(sql)
    log.info("Gold fatos: OK")


def _validar_kpis(**context):
    hook = get_hook()
    gabarito_raw = json.loads(GABARITO_PATH.read_text())
    gab = {entry["kpi"]: entry["dados"] for entry in gabarito_raw}
    erros = []

    def soma(dados, campo):
        return sum(float(r.get(campo, 0) or 0) for r in dados if r.get(campo) is not None)

    # KPI 1: saldo total por agencia
    pg1 = float(hook.get_first("SELECT SUM(saldo_total) FROM gold.vw_kpi1_saldo_por_agencia")[0])
    gab1 = soma(gab[1], "saldo_total")
    if abs(pg1 - gab1) > 0.02:
        erros.append(f"KPI1 saldo_total: {pg1:.2f} != {gab1:.2f}")

    # KPI 2_3: volume de transacoes por mes e tipo
    pg23 = float(hook.get_first("SELECT SUM(volume_total) FROM gold.vw_kpi2_3_transacoes_por_mes")[0])
    gab23 = soma(gab["2_3"], "volume")
    if abs(pg23 - gab23) > 0.02:
        erros.append(f"KPI2_3 volume_total: {pg23:.2f} != {gab23:.2f}")

    # KPI 4: conversao de propostas — compara por contagens ordenadas (evita encoding)
    pg4_counts = sorted(
        int(r[0]) for r in hook.get_records(
            "SELECT qtd_propostas FROM gold.vw_kpi4_conversao_propostas"
        )
    )
    gab4_counts = sorted(int(r["qtd_propostas"]) for r in gab[4])
    if pg4_counts != gab4_counts:
        erros.append(f"KPI4 counts: {pg4_counts} != {gab4_counts}")

    # KPI 5: ranking de agencias (quantidade + lider)
    rows_pg5 = hook.get_records(
        "SELECT cod_agencia FROM gold.vw_kpi5_ranking_agencias ORDER BY ranking"
    )
    gab5 = gab[5]
    if len(rows_pg5) != len(gab5):
        erros.append(f"KPI5 qtd agencias: {len(rows_pg5)} != {len(gab5)}")
    elif str(rows_pg5[0][0]) != str(gab5[0]["cod_agencia"]):
        erros.append(f"KPI5 top1: {rows_pg5[0][0]} != {gab5[0]['cod_agencia']}")

    # KPI 6: carteira por colaborador (soma do saldo gerido total)
    pg6 = float(hook.get_first("SELECT SUM(saldo_gerido) FROM gold.vw_kpi6_carteira_colaborador")[0])
    gab6 = soma(gab[6], "saldo_gerido")
    if abs(pg6 - gab6) > max(gab6 * 0.01, 0.02):
        erros.append(f"KPI6 saldo_gerido: {pg6:.2f} != {gab6:.2f}")

    # KPI 7: segmentacao por faixa etaria
    rows_pg7 = {
        r[0]: int(r[1])
        for r in hook.get_records(
            "SELECT faixa_etaria, qtd_clientes FROM gold.vw_kpi7_segmentacao_clientes"
        )
    }
    for row_gab in gab[7]:
        fx = row_gab["faixa_etaria"]
        qtd_pg = rows_pg7.get(fx, 0)
        qtd_gab = int(row_gab["qtd_clientes"])
        if qtd_pg != qtd_gab:
            erros.append(f"KPI7 faixa={fx}: {qtd_pg} != {qtd_gab}")

    # KPI 8: correcao IPCA (soma do volume nominal)
    pg8 = float(hook.get_first("SELECT SUM(volume_nominal) FROM gold.vw_kpi8_correcao_ipca")[0])
    gab8 = soma(gab[8], "volume_nominal")
    if abs(pg8 - gab8) > 0.02:
        erros.append(f"KPI8 volume_nominal: {pg8:.2f} != {gab8:.2f}")

    if erros:
        raise ValueError("Validacao falhou:\n" + "\n".join(erros))

    resultado = {"status": "APROVADO", "kpis_verificados": 8}
    context["ti"].xcom_push(key="validacao", value=resultado)
    log.info("Validacao APROVADA: todos os 8 KPIs OK")


# ── DAG ───────────────────────────────────────────────────────────────────────

with DAG(
    dag_id="banvic_pipeline",
    description="BanVic 360 — Bronze -> Silver -> Gold -> Validacao KPIs",
    default_args={
        "owner": "banvic",
        "retries": 2,
        "retry_delay": timedelta(minutes=3),
        "email_on_failure": False,
    },
    schedule_interval="0 6 * * *",
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["banvic", "etl", "gold"],
) as dag:

    check_bronze = ShortCircuitOperator(
        task_id="check_bronze",
        python_callable=_check_bronze,
    )

    preparar = PythonOperator(
        task_id="preparar_ambiente",
        python_callable=_preparar_ambiente,
    )

    with TaskGroup("silver", tooltip="Bronze -> Silver (paralelo por entidade)") as tg_silver:
        entidades = ["clientes", "contas", "transacoes", "agencias", "colaboradores", "propostas", "externos"]
        tasks_silver = [
            PythonOperator(
                task_id=ent,
                python_callable=_silver_task,
                op_kwargs={"entity": ent},
            )
            for ent in entidades
        ]
        indices = PythonOperator(
            task_id="indices",
            python_callable=_silver_task,
            op_kwargs={"entity": "indices"},
        )
        tasks_silver >> indices

    with TaskGroup("gold", tooltip="Silver -> Gold dims e fatos") as tg_gold:
        dims = PythonOperator(
            task_id="dims",
            python_callable=_gold_dims,
        )
        fatos = PythonOperator(
            task_id="fatos",
            python_callable=_gold_fatos,
        )
        dims >> fatos

    validar = PythonOperator(
        task_id="validar_kpis",
        python_callable=_validar_kpis,
    )

    check_bronze >> preparar >> tg_silver >> tg_gold >> validar
