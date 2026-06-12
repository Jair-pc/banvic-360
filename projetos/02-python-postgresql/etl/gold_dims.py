"""
BanVic 360 -- Projeto 2 -- Dimensoes Gold
Popula dims a partir de Silver usando pandas + SQLAlchemy.
Replica a logica de projetos/01-sql-puro/sql/01_populate_dims.sql.
"""
import pandas as pd
from sqlalchemy import text

from .conexao import get_engine, truncar


def _popular_dim_tempo(engine):
    """Enriquece dim_tempo com macroeconomia (Selic/CDI/PTAX/IPCA) e feriados."""

    def _update_from_df(df: pd.DataFrame, col_data: str, updates: dict, engine):
        """Escreve DataFrame em tabela temporaria e executa UPDATE FROM."""
        df.to_sql("_tmp_dim_tempo", engine, schema="silver", if_exists="replace",
                  index=False, method="multi", chunksize=10000)
        set_clause = ", ".join(f"{k} = t.{v}" for k, v in updates.items())
        sql = f"""
            UPDATE gold.dim_tempo d
            SET {set_clause}
            FROM silver._tmp_dim_tempo t
            WHERE d.data = t.{col_data}
        """
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.execute(text("DROP TABLE IF EXISTS silver._tmp_dim_tempo"))

    # Selic diaria
    selic = pd.read_sql(
        "SELECT data::date AS dt, taxa_selic::numeric AS taxa_selic FROM bronze.selic "
        "WHERE taxa_selic ~ '^-?[0-9]+\\.?[0-9]*$'",
        engine,
    )
    selic.columns = ["dt", "taxa_selic"]
    _update_from_df(selic, "dt", {"taxa_selic": "taxa_selic"}, engine)

    # CDI diario
    cdi = pd.read_sql(
        "SELECT data::date AS dt, taxa_cdi::numeric AS taxa_cdi FROM bronze.cdi "
        "WHERE taxa_cdi ~ '^-?[0-9]+\\.?[0-9]*$'",
        engine,
    )
    if not cdi.empty:
        cdi.columns = ["dt", "taxa_cdi"]
        _update_from_df(cdi, "dt", {"taxa_cdi": "taxa_cdi"}, engine)

    # PTAX dolar
    dolar = pd.read_sql(
        "SELECT data::date AS dt, cotacao_media::numeric AS cotacao_dolar FROM bronze.dolar_ptax "
        "WHERE cotacao_media ~ '^-?[0-9]+\\.?[0-9]*$'",
        engine,
    )
    if not dolar.empty:
        dolar.columns = ["dt", "cotacao_dolar"]
        _update_from_df(dolar, "dt", {"cotacao_dolar": "cotacao_dolar"}, engine)

    # PTAX euro
    euro = pd.read_sql(
        "SELECT data::date AS dt, cotacao_media::numeric AS cotacao_euro FROM bronze.euro_ptax "
        "WHERE cotacao_media ~ '^-?[0-9]+\\.?[0-9]*$'",
        engine,
    )
    if not euro.empty:
        euro.columns = ["dt", "cotacao_euro"]
        _update_from_df(euro, "dt", {"cotacao_euro": "cotacao_euro"}, engine)

    # IPCA mensal (propagar para todos os dias do mes)
    ipca = pd.read_sql(
        "SELECT ano::smallint AS ano, mes_num::smallint AS mes, "
        "no_mes::numeric AS ipca_mes, acumulado_12m::numeric AS ipca_acum_12m, "
        "indice::numeric AS indice_ipca FROM bronze.ipca "
        "WHERE indice ~ '^-?[0-9]+\\.?[0-9]*$'",
        engine,
    )
    if not ipca.empty:
        ipca.to_sql("_tmp_ipca", engine, schema="silver", if_exists="replace",
                    index=False, method="multi")
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE gold.dim_tempo d
                SET ipca_mes      = t.ipca_mes,
                    ipca_acum_12m = t.ipca_acum_12m,
                    indice_ipca   = t.indice_ipca
                FROM silver._tmp_ipca t
                WHERE d.ano = t.ano AND d.mes = t.mes
            """))
            conn.execute(text("DROP TABLE IF EXISTS silver._tmp_ipca"))

    # Feriados
    feriados = pd.read_sql(
        "SELECT data::date AS dt, nome, tipo FROM bronze.feriados",
        engine,
    )
    if not feriados.empty:
        feriados.columns = ["dt", "nome_feriado", "tipo_feriado"]
        feriados["eh_feriado"]  = True
        feriados["eh_dia_util"] = False
        feriados.to_sql("_tmp_feriados", engine, schema="silver", if_exists="replace",
                        index=False, method="multi")
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE gold.dim_tempo d
                SET eh_feriado   = t.eh_feriado,
                    nome_feriado = t.nome_feriado,
                    tipo_feriado = t.tipo_feriado,
                    eh_dia_util  = t.eh_dia_util
                FROM silver._tmp_feriados t
                WHERE d.data = t.dt
            """))
            conn.execute(text("DROP TABLE IF EXISTS silver._tmp_feriados"))

    print("  gold.dim_tempo: atualizada (Selic/CDI/PTAX/IPCA/Feriados)")


def _popular_dim_municipio(engine):
    truncar("gold.dim_municipio", engine, cascade=True)
    df = pd.read_sql("SELECT * FROM silver.municipios_clean", engine)
    out = df[[
        "codigo_ibge", "municipio", "uf",
        "populacao", "ano_populacao", "pib_total", "pib_per_capita", "ano_pib",
    ]]
    out.to_sql("dim_municipio", engine, schema="gold", if_exists="append",
               index=False, method="multi", chunksize=5000)
    print(f"  gold.dim_municipio: {len(out):,} linhas")


def _popular_dim_agencia(engine):
    truncar("gold.dim_agencia", engine, cascade=True)
    df = pd.read_sql("SELECT * FROM silver.agencias_clean", engine)
    out = df[[
        "cod_agencia", "nome", "tipo_agencia", "cidade", "uf", "regiao",
        "data_abertura", "eh_ativa", "meta_comercial_mensal", "latitude", "longitude",
    ]].copy()
    out.insert(0, "sk_agencia", range(1, len(out) + 1))
    out.to_sql("dim_agencia", engine, schema="gold", if_exists="append",
               index=False, method="multi")
    print(f"  gold.dim_agencia: {len(out):,} linhas")


def _popular_dim_colaborador(engine):
    truncar("gold.dim_colaborador", engine, cascade=True)
    colab   = pd.read_sql("SELECT * FROM silver.colaboradores_clean", engine)
    dim_ag  = pd.read_sql("SELECT sk_agencia, cod_agencia FROM gold.dim_agencia", engine)

    colab["cod_agencia"] = pd.to_numeric(colab["cod_agencia"], errors="coerce").astype("Int32")
    dim_ag["cod_agencia"] = dim_ag["cod_agencia"].astype("Int32")

    merged = colab.merge(dim_ag, on="cod_agencia", how="left")
    merged.rename(columns={"sk_agencia": "sk_agencia_principal"}, inplace=True)

    out = merged[[
        "cod_colaborador", "primeiro_nome", "ultimo_nome", "cpf", "email",
        "data_nascimento", "cargo", "departamento", "nivel_hierarquico",
        "salario_base", "data_admissao", "data_demissao",
        "eh_ativo", "sk_agencia_principal", "cidade", "uf",
    ]].copy()
    out.insert(0, "sk_colaborador", range(1, len(out) + 1))
    out.to_sql("dim_colaborador", engine, schema="gold", if_exists="append",
               index=False, method="multi", chunksize=5000)
    print(f"  gold.dim_colaborador: {len(out):,} linhas")


def _popular_dim_cliente(engine):
    truncar("gold.dim_cliente", engine, cascade=True)

    # Clientes originais
    orig = pd.read_sql("SELECT * FROM silver.clientes_clean", engine)
    orig["cpf"]          = orig["cpf_formatado"]
    orig["cep"]          = orig["cep_digits"]
    orig["data_inicio_vigencia"] = orig["data_inclusao"]
    orig["data_fim_vigencia"]    = pd.to_datetime("9999-12-31").date()
    orig["eh_registro_atual"]    = True
    orig_out = orig[[
        "cod_cliente", "primeiro_nome", "ultimo_nome", "cpf", "tipo_pessoa", "email",
        "data_nascimento", "idade", "faixa_etaria", "cep", "data_inclusao",
        "data_inicio_vigencia", "data_fim_vigencia", "eh_registro_atual",
    ]].copy()
    orig_out.insert(0, "sk_cliente", range(1, len(orig_out) + 1))
    orig_out.to_sql("dim_cliente", engine, schema="gold", if_exists="append",
                    index=False, method="multi", chunksize=5000)

    # Clientes sinteticos
    sint = pd.read_sql("SELECT * FROM silver.clientes_sinteticos_clean", engine)
    sint["data_inicio_vigencia"] = sint["data_inclusao"]
    sint["data_fim_vigencia"]    = pd.to_datetime("9999-12-31").date()
    sint["eh_registro_atual"]    = True
    sint_out = sint[[
        "cod_cliente", "primeiro_nome", "ultimo_nome", "tipo_pessoa", "email",
        "data_nascimento", "idade", "faixa_etaria",
        "cidade", "uf", "renda_mensal", "faixa_renda",
        "profissao", "escolaridade", "score_credito", "faixa_score",
        "data_inclusao", "data_inicio_vigencia", "data_fim_vigencia", "eh_registro_atual",
    ]].copy()
    sint_out.insert(0, "sk_cliente", range(len(orig_out) + 1, len(orig_out) + len(sint_out) + 1))
    sint_out.to_sql("dim_cliente", engine, schema="gold", if_exists="append",
                    index=False, method="multi", chunksize=5000)

    # Deduplicar: manter sk maior por cod_cliente (inserido por ultimo)
    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM gold.dim_cliente
            WHERE sk_cliente IN (
                SELECT sk_cliente FROM (
                    SELECT sk_cliente,
                           ROW_NUMBER() OVER (PARTITION BY cod_cliente ORDER BY sk_cliente DESC) AS rn
                    FROM gold.dim_cliente
                    WHERE eh_registro_atual = TRUE
                ) ranked WHERE rn > 1
            )
        """))

    total = pd.read_sql("SELECT COUNT(*) AS n FROM gold.dim_cliente", engine).iloc[0]["n"]
    print(f"  gold.dim_cliente: {total:,} linhas (apos dedup)")


def _popular_dim_canal(engine):
    truncar("gold.dim_canal", engine, cascade=True)
    canais = pd.read_sql(
        "SELECT DISTINCT canal AS nome_canal FROM silver.transacoes_clean ORDER BY canal",
        engine,
    )
    tipo_map = {
        "Pix": "Transferencia", "TED": "Transferencia", "DOC": "Transferencia",
        "Compra Credito": "Cartao",  "Compra Debito": "Cartao",
        "Saque": "Caixa",            "Deposito Especie": "Caixa",
        "Pagamento Boleto": "Boleto",
    }
    canais["tipo_canal"] = canais["nome_canal"].map(tipo_map).fillna("Digital")
    canais.insert(0, "sk_canal", range(1, len(canais) + 1))
    canais.to_sql("dim_canal", engine, schema="gold", if_exists="append",
                  index=False, method="multi")
    print(f"  gold.dim_canal: {len(canais):,} linhas")


# ─── Orquestrador ─────────────────────────────────────────────────────────────

def popular_dims(engine=None):
    if engine is None:
        engine = get_engine()
    _popular_dim_tempo(engine)
    _popular_dim_municipio(engine)
    _popular_dim_agencia(engine)
    _popular_dim_colaborador(engine)
    _popular_dim_cliente(engine)
    _popular_dim_canal(engine)
