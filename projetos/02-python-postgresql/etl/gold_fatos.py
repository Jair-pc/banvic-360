"""
BanVic 360 -- Projeto 2 -- Fatos Gold
Popula fatos via pandas merge (replica os JOINs do SQL do Projeto 1).
Replica a logica de projetos/01-sql-puro/sql/02_populate_fatos.sql.
"""
import pandas as pd

from .conexao import get_engine


def _ler_dim_tempo(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT sk_tempo, data FROM gold.dim_tempo", engine)


def _ler_dim_cliente(engine) -> pd.DataFrame:
    return pd.read_sql(
        "SELECT sk_cliente, cod_cliente FROM gold.dim_cliente WHERE eh_registro_atual = TRUE",
        engine,
    )


def _ler_dim_agencia(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT sk_agencia, cod_agencia FROM gold.dim_agencia", engine)


def _ler_dim_colaborador(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT sk_colaborador, cod_colaborador FROM gold.dim_colaborador", engine)


def _ler_dim_canal(engine) -> pd.DataFrame:
    return pd.read_sql("SELECT sk_canal, nome_canal FROM gold.dim_canal", engine)


def _popular_fato_transacoes(engine):
    tx = pd.read_sql(
        "SELECT cod_transacao, num_conta::int, data_transacao::date AS data_tx, "
        "nome_transacao, valor_transacao, flag_credito, canal FROM silver.transacoes_clean",
        engine,
    )
    contas = pd.read_sql("SELECT num_conta, cod_cliente, cod_agencia FROM silver.contas_clean", engine)
    dt    = _ler_dim_tempo(engine)
    cli   = _ler_dim_cliente(engine)
    ag    = _ler_dim_agencia(engine)
    canal = _ler_dim_canal(engine)

    # Converter ambos para string YYYY-MM-DD para merge confiavel entre versoes do pandas
    dt["data_str"]   = pd.to_datetime(dt["data"]).dt.strftime("%Y-%m-%d")
    tx["data_tx_str"] = pd.to_datetime(tx["data_tx"]).dt.strftime("%Y-%m-%d")
    tx["num_conta"]   = tx["num_conta"].astype("Int32")
    contas["num_conta"]   = contas["num_conta"].astype("Int32")
    contas["cod_cliente"] = contas["cod_cliente"].astype("Int32")
    contas["cod_agencia"] = contas["cod_agencia"].astype("Int32")
    cli["cod_cliente"]    = cli["cod_cliente"].astype("Int32")
    ag["cod_agencia"]     = ag["cod_agencia"].astype("Int32")

    df = tx.merge(dt, left_on="data_tx_str", right_on="data_str", how="inner")
    df = df.merge(contas, on="num_conta", how="inner")
    df = df.merge(cli, on="cod_cliente", how="inner")
    df = df.merge(ag,  on="cod_agencia", how="inner")
    df = df.merge(canal, left_on="canal", right_on="nome_canal", how="left")

    out = df[[
        "cod_transacao", "sk_tempo", "sk_cliente", "sk_agencia", "sk_canal",
        "num_conta", "nome_transacao", "valor_transacao", "flag_credito",
    ]].dropna(subset=["sk_tempo", "sk_cliente", "sk_agencia"])

    out.to_sql("fato_transacoes", engine, schema="gold", if_exists="append",
               index=False, method="multi", chunksize=10000)
    print(f"  gold.fato_transacoes: {len(out):,} linhas")


def _popular_fato_contas(engine):
    contas = pd.read_sql(
        "SELECT num_conta, cod_cliente, cod_agencia, cod_colaborador, "
        "saldo_total, saldo_disponivel, data_ultimo_lancamento::date AS data_ult FROM silver.contas_clean",
        engine,
    )
    dt     = _ler_dim_tempo(engine)
    cli    = _ler_dim_cliente(engine)
    ag     = _ler_dim_agencia(engine)
    col    = _ler_dim_colaborador(engine)

    dt["data_str"]        = pd.to_datetime(dt["data"]).dt.strftime("%Y-%m-%d")
    # COALESCE: contas sem data_ultimo_lancamento recebem a data de referencia (mesmo comportamento do Projeto 1)
    contas["data_ult_str"] = pd.to_datetime(contas["data_ult"]).dt.strftime("%Y-%m-%d").fillna("2026-06-10")
    contas["cod_cliente"]    = contas["cod_cliente"].astype("Int32")
    contas["cod_agencia"]    = contas["cod_agencia"].astype("Int32")
    contas["cod_colaborador"] = contas["cod_colaborador"].astype("Int32")
    cli["cod_cliente"]       = cli["cod_cliente"].astype("Int32")
    ag["cod_agencia"]        = ag["cod_agencia"].astype("Int32")
    col["cod_colaborador"]   = col["cod_colaborador"].astype("Int32")

    df = contas.merge(dt, left_on="data_ult_str", right_on="data_str", how="inner")
    df = df.merge(cli, on="cod_cliente", how="inner")
    df = df.merge(ag,  on="cod_agencia", how="inner")
    df = df.merge(col, on="cod_colaborador", how="left")

    # Snapshot corrente: todas as contas sao ativas
    df["eh_conta_ativa"] = True

    out = df[[
        "sk_tempo", "sk_cliente", "sk_agencia", "sk_colaborador",
        "num_conta", "saldo_total", "saldo_disponivel", "eh_conta_ativa",
    ]].dropna(subset=["sk_tempo", "sk_cliente", "sk_agencia"])

    out.to_sql("fato_contas", engine, schema="gold", if_exists="append",
               index=False, method="multi", chunksize=5000)
    print(f"  gold.fato_contas: {len(out):,} linhas")


def _popular_fato_propostas(engine):
    # Le da bronze (apenas propostas originais — mesma logica do Projeto 1)
    prop = pd.read_sql(
        """SELECT cod_proposta, cod_cliente, cod_colaborador,
                  data_entrada_proposta, taxa_juros_mensal,
                  valor_proposta, valor_financiamento, valor_entrada,
                  valor_prestacao, quantidade_parcelas, status_proposta
           FROM bronze.propostas_credito
           WHERE cod_proposta IS NOT NULL
             AND data_entrada_proposta IS NOT NULL""",
        engine,
    )
    dt  = _ler_dim_tempo(engine)
    cli = _ler_dim_cliente(engine)
    col = _ler_dim_colaborador(engine)

    dt["data_str"] = pd.to_datetime(dt["data"]).dt.strftime("%Y-%m-%d")
    prop["data_entrada_proposta"] = pd.to_datetime(
        prop["data_entrada_proposta"], errors="coerce"
    )
    prop["data_entrada_str"] = prop["data_entrada_proposta"].dt.strftime("%Y-%m-%d")
    prop["cod_proposta"]    = pd.to_numeric(prop["cod_proposta"], errors="coerce").astype("Int32")
    prop["cod_cliente"]     = pd.to_numeric(prop["cod_cliente"],  errors="coerce").astype("Int32")
    prop["cod_colaborador"] = pd.to_numeric(prop["cod_colaborador"], errors="coerce").astype("Int32")
    prop["valor_proposta"]      = pd.to_numeric(prop["valor_proposta"],      errors="coerce")
    prop["valor_financiamento"] = pd.to_numeric(prop["valor_financiamento"], errors="coerce")
    prop["valor_entrada"]       = pd.to_numeric(prop["valor_entrada"],       errors="coerce")
    prop["valor_prestacao"]     = pd.to_numeric(prop["valor_prestacao"],     errors="coerce")
    prop["quantidade_parcelas"] = pd.to_numeric(prop["quantidade_parcelas"], errors="coerce").astype("Int16")
    prop["taxa_juros_mensal"]   = pd.to_numeric(prop["taxa_juros_mensal"],   errors="coerce")
    prop["status_proposta"]     = prop["status_proposta"].str.strip()
    cli["cod_cliente"]    = cli["cod_cliente"].astype("Int32")
    col["cod_colaborador"] = col["cod_colaborador"].astype("Int32")

    df = prop.merge(dt, left_on="data_entrada_str", right_on="data_str", how="inner")
    df.rename(columns={"sk_tempo": "sk_tempo_entrada"}, inplace=True)
    df = df.merge(cli, on="cod_cliente", how="inner")
    df = df.merge(col, on="cod_colaborador", how="left")

    out = df[[
        "cod_proposta", "sk_tempo_entrada", "sk_cliente", "sk_colaborador",
        "status_proposta", "valor_proposta", "valor_financiamento",
        "valor_entrada", "valor_prestacao", "quantidade_parcelas", "taxa_juros_mensal",
    ]].dropna(subset=["sk_tempo_entrada", "sk_cliente"])

    out.to_sql("fato_propostas_credito", engine, schema="gold", if_exists="append",
               index=False, method="multi", chunksize=5000)
    print(f"  gold.fato_propostas_credito: {len(out):,} linhas")


# ─── Orquestrador ─────────────────────────────────────────────────────────────

def popular_fatos(engine=None):
    if engine is None:
        engine = get_engine()
    _popular_fato_transacoes(engine)
    _popular_fato_contas(engine)
    _popular_fato_propostas(engine)
