"""
BanVic 360 -- Projeto 2 -- Camada Silver
Transforma Bronze (TEXT) -> Silver (tipos corretos, padronizados).
Replica a logica de sql/02_silver/ddl_silver_transforms.sql usando pandas.
"""
import re
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import text

from .conexao import get_engine, truncar

REGIAO_MAP = {
    "SP": "Sudeste", "RJ": "Sudeste", "MG": "Sudeste", "ES": "Sudeste",
    "RS": "Sul",     "SC": "Sul",     "PR": "Sul",
    "BA": "Nordeste", "PE": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "RN": "Nordeste", "AL": "Nordeste", "SE": "Nordeste",
    "PI": "Nordeste",
    "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "DF": "Centro-Oeste",
    "AM": "Norte", "PA": "Norte", "AC": "Norte", "RO": "Norte",
    "RR": "Norte", "AP": "Norte", "TO": "Norte",
}


def _calcular_idade(dt_serie: pd.Series) -> pd.Series:
    hoje = pd.Timestamp.today().normalize()
    return ((hoje - dt_serie).dt.days // 365).astype("Int16")


def _faixa_etaria(idade: pd.Series) -> pd.Series:
    conditions = [
        (idade >= 18) & (idade <= 24),
        (idade >= 25) & (idade <= 34),
        (idade >= 35) & (idade <= 44),
        (idade >= 45) & (idade <= 54),
        (idade >= 55) & (idade <= 64),
        idade >= 65,
    ]
    choices = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    return np.select(conditions, choices, default="Menor")


def _canal_derivado(nome: pd.Series) -> pd.Series:
    nome_lower = nome.str.lower().fillna("")
    conditions = [
        nome_lower.str.contains("pix"),
        nome_lower.str.contains("ted"),
        nome_lower.str.contains("doc"),
        nome_lower.str.contains("credito"),
        nome_lower.str.contains("debito"),
        nome_lower.str.contains("saque"),
        nome_lower.str.contains("deposito"),
        nome_lower.str.contains("boleto"),
    ]
    choices = [
        "Pix", "TED", "DOC",
        "Compra Credito", "Compra Debito",
        "Saque", "Deposito Especie", "Pagamento Boleto",
    ]
    return np.select(conditions, choices, default="Outros")


def _silver_ts() -> pd.Timestamp:
    return pd.Timestamp.now()


# ─── Transforms individuais ───────────────────────────────────────────────────

def _transform_clientes(engine) -> int:
    df = pd.read_sql(
        "SELECT * FROM bronze.clientes WHERE cod_cliente IS NOT NULL AND cpfcnpj IS NOT NULL",
        engine,
    )
    df["cod_cliente"]   = pd.to_numeric(df["cod_cliente"], errors="coerce").astype("Int32")
    df["primeiro_nome"] = df["primeiro_nome"].str.strip()
    df["ultimo_nome"]   = df["ultimo_nome"].str.strip()
    df["email"]         = df["email"].str.strip().str.lower()
    df["tipo_pessoa"]   = df["tipo_cliente"].str.strip().str.upper()
    df["data_inclusao"] = pd.to_datetime(df["data_inclusao"], errors="coerce").dt.date
    df["cpf_digits"]    = df["cpfcnpj"].str.replace(r"[^0-9]", "", regex=True)
    df["cpf_formatado"] = df["cpfcnpj"]
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce")
    df["idade"]         = _calcular_idade(df["data_nascimento"])
    df["faixa_etaria"]  = _faixa_etaria(df["idade"])
    df["data_nascimento"] = df["data_nascimento"].dt.date
    df["endereco"]      = df["endereco"].str.strip()
    df["cep_digits"]    = df["cep"].str.replace(r"[^0-9]", "", regex=True)
    df["_silver_ts"]    = _silver_ts()

    out = df[[
        "cod_cliente", "primeiro_nome", "ultimo_nome", "email", "tipo_pessoa",
        "data_inclusao", "cpf_digits", "cpf_formatado", "data_nascimento",
        "idade", "faixa_etaria", "endereco", "cep_digits", "_silver_ts",
    ]].dropna(subset=["cod_cliente"])

    out.to_sql("clientes_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi", chunksize=5000)
    return len(out)


def _transform_clientes_sinteticos(engine) -> int:
    df = pd.read_sql(
        "SELECT * FROM bronze.clientes_sinteticos WHERE cod_cliente IS NOT NULL",
        engine,
    )
    df["cod_cliente"]     = pd.to_numeric(df["cod_cliente"], errors="coerce").astype("Int32")
    df["primeiro_nome"]   = df["primeiro_nome"].str.strip()
    df["ultimo_nome"]     = df["ultimo_nome"].str.strip()
    df["email"]           = df["email"].str.strip().str.lower()
    df["tipo_pessoa"]     = df["tipo_cliente"].str.upper()
    df["data_inclusao"]   = pd.to_datetime(df["data_inclusao"], errors="coerce").dt.date
    df["cpf_formatado"]   = df["cpfcnpj"]
    df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce").dt.date
    df["idade"]           = pd.to_numeric(df["idade"], errors="coerce").astype("Int16")
    df["uf"]              = df["uf"].str.upper()
    df["renda_mensal"]    = pd.to_numeric(df["renda_mensal"], errors="coerce")
    df["score_credito"]   = pd.to_numeric(df["score_credito"], errors="coerce").astype("Int16")
    df["_silver_ts"]      = _silver_ts()

    out = df[[
        "cod_cliente", "primeiro_nome", "ultimo_nome", "email", "tipo_pessoa",
        "data_inclusao", "cpf_formatado", "data_nascimento", "idade", "faixa_etaria",
        "cidade", "uf", "cep", "renda_mensal", "faixa_renda", "profissao",
        "escolaridade", "score_credito", "faixa_score", "_silver_ts",
    ]].dropna(subset=["cod_cliente"])

    out.to_sql("clientes_sinteticos_clean", engine, schema="silver",
               if_exists="replace", index=False, method="multi", chunksize=5000)
    return len(out)


def _transform_contas(engine) -> int:
    df = pd.read_sql("SELECT * FROM bronze.contas WHERE num_conta IS NOT NULL", engine)

    # Filtrar saldo valido (regex numerico)
    mask = df["saldo_total"].str.match(r"^-?[0-9]+\.?[0-9]*$", na=False)
    df = df[mask].copy()

    df["num_conta"]     = pd.to_numeric(df["num_conta"], errors="coerce").astype("Int32")
    df["cod_cliente"]   = pd.to_numeric(df["cod_cliente"], errors="coerce").astype("Int32")
    df["cod_agencia"]   = pd.to_numeric(df["cod_agencia"], errors="coerce").astype("Int32")
    df["cod_colaborador"] = pd.to_numeric(df["cod_colaborador"], errors="coerce").astype("Int32")
    df["tipo_conta"]    = df["tipo_conta"].str.strip()
    df["data_abertura"] = pd.to_datetime(df["data_abertura"], errors="coerce").dt.date
    df["saldo_total"]       = pd.to_numeric(df["saldo_total"]).round(2)
    df["saldo_disponivel"]  = pd.to_numeric(df["saldo_disponivel"]).round(2)
    df["data_ultimo_lancamento"] = pd.to_datetime(
        df["data_ultimo_lancamento"], errors="coerce"
    ).dt.date

    # Flag ativa relativa ao dataset (nao CURRENT_DATE)
    max_date = df["data_ultimo_lancamento"].max()
    cutoff = pd.to_datetime(max_date) - pd.Timedelta(days=90)
    df["eh_conta_ativa"] = pd.to_datetime(df["data_ultimo_lancamento"]) >= cutoff
    df["_silver_ts"] = _silver_ts()

    out = df[[
        "num_conta", "cod_cliente", "cod_agencia", "cod_colaborador",
        "tipo_conta", "data_abertura", "saldo_total", "saldo_disponivel",
        "data_ultimo_lancamento", "eh_conta_ativa", "_silver_ts",
    ]].dropna(subset=["num_conta"])

    out.to_sql("contas_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi", chunksize=5000)
    return len(out)


def _transform_transacoes(engine) -> int:
    df = pd.read_sql(
        "SELECT * FROM bronze.transacoes WHERE cod_transacao IS NOT NULL",
        engine,
    )
    # Filtrar valor numerico e != 0
    mask = df["valor_transacao"].str.match(r"^-?[0-9]+\.?[0-9]*$", na=False)
    df = df[mask].copy()
    df["valor_transacao"] = pd.to_numeric(df["valor_transacao"])
    df = df[df["valor_transacao"] != 0].copy()

    df["cod_transacao"]   = pd.to_numeric(df["cod_transacao"], errors="coerce").astype("Int32")
    df["num_conta"]       = pd.to_numeric(df["num_conta"], errors="coerce").astype("Int32")
    df["data_transacao"]  = pd.to_datetime(df["data_transacao"], errors="coerce")
    df["mes_referencia"]  = df["data_transacao"].dt.to_period("M").dt.to_timestamp().dt.date
    df["nome_transacao"]  = df["nome_transacao"].str.strip()
    df["valor_transacao"] = df["valor_transacao"].round(2)
    df["valor_absoluto"]  = df["valor_transacao"].abs()
    df["flag_credito"]    = df["valor_transacao"] >= 0
    df["canal"]           = _canal_derivado(df["nome_transacao"])
    df["_silver_ts"]      = _silver_ts()

    out = df[[
        "cod_transacao", "num_conta", "data_transacao", "mes_referencia",
        "nome_transacao", "valor_transacao", "valor_absoluto",
        "flag_credito", "canal", "_silver_ts",
    ]].dropna(subset=["cod_transacao"])

    out.to_sql("transacoes_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi", chunksize=10000)
    return len(out)


def _transform_agencias(engine) -> int:
    ag  = pd.read_sql("SELECT * FROM bronze.agencias WHERE cod_agencia IS NOT NULL", engine)
    exp = pd.read_sql(
        "SELECT cod_agencia, meta_comercial_mensal, latitude, longitude FROM bronze.agencias_expandidas",
        engine,
    )
    ag["cod_agencia"]  = pd.to_numeric(ag["cod_agencia"]).astype(int)
    exp["cod_agencia"] = pd.to_numeric(exp["cod_agencia"]).astype(int)

    df = ag.merge(exp, on="cod_agencia", how="left")
    df["nome"]       = df["nome"].str.strip()
    df["tipo_agencia"] = df["tipo_agencia"].str.strip().str.upper()
    df["uf"]         = df["uf"].str.upper().str.strip()
    df["regiao"]     = df["uf"].map(REGIAO_MAP).fillna("Sudeste")
    df["data_abertura"] = pd.to_datetime(df["data_abertura"], errors="coerce").dt.date
    df["meta_comercial_mensal"] = pd.to_numeric(
        df["meta_comercial_mensal"], errors="coerce"
    ).fillna(500000)
    df["latitude"]   = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"]  = pd.to_numeric(df["longitude"], errors="coerce")
    df["eh_ativa"]   = True
    df["_silver_ts"] = _silver_ts()

    out = df[[
        "cod_agencia", "nome", "tipo_agencia", "cidade", "uf", "regiao",
        "data_abertura", "meta_comercial_mensal", "latitude", "longitude",
        "eh_ativa", "_silver_ts",
    ]]
    out.to_sql("agencias_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi")
    return len(out)


def _transform_colaboradores(engine) -> int:
    exp = pd.read_sql(
        "SELECT * FROM bronze.colaboradores_expandidos WHERE cod_colaborador IS NOT NULL",
        engine,
    )
    # Originais nao presentes no expandido
    orig = pd.read_sql(
        """SELECT c.* FROM bronze.colaboradores c
           WHERE NOT EXISTS (
               SELECT 1 FROM bronze.colaboradores_expandidos e
               WHERE e.cod_colaborador = c.cod_colaborador
           )""",
        engine,
    )

    def _prep_exp(df):
        df = df.copy()
        df["cod_colaborador"]  = pd.to_numeric(df["cod_colaborador"], errors="coerce").astype("Int32")
        df["email"]            = df["email"].str.lower()
        df["uf"]               = df["uf"].str.upper()
        df["nivel_hierarquico"] = pd.to_numeric(df["nivel_hierarquico"], errors="coerce").astype("Int16")
        df["salario_base"]     = pd.to_numeric(df["salario_base"], errors="coerce")
        df["cod_agencia"]      = pd.to_numeric(df["cod_agencia"], errors="coerce").astype("Int32")
        df["data_admissao"]    = pd.to_datetime(df["data_admissao"], errors="coerce").dt.date
        df["data_nascimento"]  = pd.to_datetime(df["data_nascimento"], errors="coerce").dt.date
        df["data_demissao"]    = pd.to_datetime(
            df["data_demissao"].replace("", pd.NA), errors="coerce"
        ).dt.date
        df["eh_ativo"]         = df["eh_ativo"].astype(str).str.lower().isin(["true", "1", "t"])
        df["_silver_ts"]       = _silver_ts()
        cols = [
            "cod_colaborador", "primeiro_nome", "ultimo_nome", "email", "cpf",
            "data_nascimento", "cidade", "uf", "regiao", "cargo",
            "nivel_hierarquico", "departamento", "salario_base", "cod_agencia",
            "data_admissao", "data_demissao", "eh_ativo", "_silver_ts",
        ]
        return df[[c for c in cols if c in df.columns]]

    def _prep_orig(df):
        df = df.copy()
        df["cod_colaborador"] = pd.to_numeric(df["cod_colaborador"], errors="coerce").astype("Int32")
        df["email"]           = df["email"].str.lower()
        df["data_nascimento"] = pd.to_datetime(df["data_nascimento"], errors="coerce").dt.date
        for col in ["cidade", "uf", "regiao", "cargo", "nivel_hierarquico",
                    "departamento", "salario_base", "cod_agencia",
                    "data_admissao", "data_demissao"]:
            if col not in df.columns:
                df[col] = None
        df["eh_ativo"]   = True
        df["_silver_ts"] = _silver_ts()
        cols = [
            "cod_colaborador", "primeiro_nome", "ultimo_nome", "email", "cpf",
            "data_nascimento", "cidade", "uf", "regiao", "cargo",
            "nivel_hierarquico", "departamento", "salario_base", "cod_agencia",
            "data_admissao", "data_demissao", "eh_ativo", "_silver_ts",
        ]
        return df[[c for c in cols if c in df.columns]]

    out = pd.concat([_prep_exp(exp), _prep_orig(orig)], ignore_index=True)
    out.to_sql("colaboradores_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi", chunksize=5000)
    return len(out)


def _transform_propostas(engine) -> int:
    def _prep(df):
        df = df.copy()
        df["cod_proposta"]        = pd.to_numeric(df["cod_proposta"], errors="coerce").astype("Int32")
        df["cod_cliente"]         = pd.to_numeric(df["cod_cliente"], errors="coerce").astype("Int32")
        df["cod_colaborador"]     = pd.to_numeric(df["cod_colaborador"], errors="coerce").astype("Int32")
        df["data_entrada_proposta"] = pd.to_datetime(df["data_entrada_proposta"], errors="coerce").dt.date
        df["taxa_juros_mensal"]   = pd.to_numeric(df["taxa_juros_mensal"], errors="coerce")
        df["valor_proposta"]      = pd.to_numeric(df["valor_proposta"], errors="coerce")
        df["valor_financiamento"] = pd.to_numeric(df["valor_financiamento"], errors="coerce")
        df["valor_entrada"]       = pd.to_numeric(df["valor_entrada"], errors="coerce")
        df["valor_prestacao"]     = pd.to_numeric(df["valor_prestacao"], errors="coerce")
        df["quantidade_parcelas"] = pd.to_numeric(df["quantidade_parcelas"], errors="coerce").astype("Int16")
        df["carencia_dias"]       = pd.to_numeric(
            df["carencia"].replace("", "0"), errors="coerce"
        ).fillna(0).astype("Int16")
        df["status_proposta"]     = df["status_proposta"].str.strip()
        df["_silver_ts"]          = _silver_ts()
        return df[[
            "cod_proposta", "cod_cliente", "cod_colaborador",
            "data_entrada_proposta", "taxa_juros_mensal",
            "valor_proposta", "valor_financiamento", "valor_entrada",
            "valor_prestacao", "quantidade_parcelas", "carencia_dias",
            "status_proposta", "_silver_ts",
        ]]

    orig = pd.read_sql(
        "SELECT * FROM bronze.propostas_credito WHERE cod_proposta IS NOT NULL",
        engine,
    )
    orig = orig[orig["valor_proposta"].str.match(r"^[0-9]+\.?[0-9]*$", na=False)]

    sint = pd.read_sql(
        "SELECT *, '' AS carencia FROM bronze.propostas_sinteticas WHERE cod_proposta IS NOT NULL",
        engine,
    )
    if "carencia" not in sint.columns:
        sint["carencia"] = "0"

    out = pd.concat([_prep(orig), _prep(sint)], ignore_index=True)
    out.to_sql("propostas_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi", chunksize=5000)
    return len(out)


def _transform_ipca(engine) -> int:
    real = pd.read_sql(
        "SELECT * FROM bronze.ipca WHERE data ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'",
        engine,
    )
    real["tipo"] = "REAL"

    proj = pd.read_sql(
        "SELECT * FROM bronze.ipca_projetado WHERE tipo = 'PROJECAO'",
        engine,
    )

    def _prep(df):
        df = df.copy()
        df["data"]       = pd.to_datetime(df["data"], errors="coerce").dt.date
        df["ano"]        = pd.to_numeric(df["ano"], errors="coerce").astype("Int16")
        df["mes_num"]    = pd.to_numeric(df["mes_num"], errors="coerce").astype("Int16")
        df["indice"]     = pd.to_numeric(df["indice"], errors="coerce")
        df["no_mes"]     = pd.to_numeric(df["no_mes"], errors="coerce")
        df["acumulado_12m"] = pd.to_numeric(df["acumulado_12m"], errors="coerce")
        df["acumulado_ano"] = pd.to_numeric(df["acumulado_ano"], errors="coerce")
        df["_silver_ts"] = _silver_ts()
        return df[["data", "ano", "mes", "mes_num", "indice", "no_mes",
                   "acumulado_12m", "acumulado_ano", "tipo", "_silver_ts"]]

    out = pd.concat([_prep(real), _prep(proj)], ignore_index=True)
    out.to_sql("ipca_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi")
    return len(out)


def _transform_selic(engine) -> int:
    real = pd.read_sql("SELECT *, 'REAL' AS tipo FROM bronze.selic", engine)
    proj = pd.read_sql(
        "SELECT * FROM bronze.selic_projetada WHERE tipo = 'PROJECAO'",
        engine,
    )

    def _prep(df):
        df = df.copy()
        df["data"]       = pd.to_datetime(df["data"], errors="coerce").dt.date
        df["taxa_selic"]    = pd.to_numeric(df["taxa_selic"], errors="coerce")
        df["taxa_selic_aa"] = df["taxa_selic"] * 252 * 100
        df["_silver_ts"] = _silver_ts()
        return df[["data", "taxa_selic", "taxa_selic_aa", "tipo", "_silver_ts"]]

    out = pd.concat([_prep(real), _prep(proj)], ignore_index=True)
    out.to_sql("selic_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi")
    return len(out)


def _transform_municipios(engine) -> int:
    mun = pd.read_sql(
        "SELECT * FROM bronze.municipios WHERE codigo_ibge IS NOT NULL",
        engine,
    )
    pop = pd.read_sql(
        "SELECT codigo_ibge, populacao, ano FROM bronze.populacao",
        engine,
    )
    pib = pd.read_sql(
        "SELECT codigo_ibge, pib_total, pib_per_capita, ano FROM bronze.pib_municipal",
        engine,
    )

    # Pegar populacao mais recente por municipio
    pop["ano"] = pd.to_numeric(pop["ano"], errors="coerce")
    pop_latest = pop.loc[pop.groupby("codigo_ibge")["ano"].idxmax()].copy()
    pop_latest.columns = ["codigo_ibge", "populacao", "ano_populacao"]

    pib["ano"] = pd.to_numeric(pib["ano"], errors="coerce")
    pib_latest = pib.loc[pib.groupby("codigo_ibge")["ano"].idxmax()].copy()
    pib_latest.columns = ["codigo_ibge", "pib_total", "pib_per_capita", "ano_pib"]

    mun["codigo_ibge"] = pd.to_numeric(mun["codigo_ibge"], errors="coerce").astype("Int32")
    pop_latest["codigo_ibge"] = pd.to_numeric(pop_latest["codigo_ibge"], errors="coerce").astype("Int32")
    pib_latest["codigo_ibge"] = pd.to_numeric(pib_latest["codigo_ibge"], errors="coerce").astype("Int32")

    df = mun.merge(pop_latest, on="codigo_ibge", how="left")
    df = df.merge(pib_latest, on="codigo_ibge", how="left")
    df["uf"]     = df["uf"].str.upper()
    df["regiao"] = df["uf"].map(REGIAO_MAP).fillna("Sudeste")
    df["pib_total"]     = pd.to_numeric(df["pib_total"],     errors="coerce")
    df["pib_per_capita"] = pd.to_numeric(df["pib_per_capita"], errors="coerce")
    df["populacao"]     = pd.to_numeric(df["populacao"],     errors="coerce").astype("Int32")
    df["ano_populacao"] = pd.to_numeric(df.get("ano_populacao"), errors="coerce").astype("Int16")
    df["ano_pib"]       = pd.to_numeric(df.get("ano_pib"),       errors="coerce").astype("Int16")
    df["_silver_ts"]    = _silver_ts()

    out = df[[
        "codigo_ibge", "municipio", "uf", "regiao",
        "populacao", "ano_populacao", "pib_total", "pib_per_capita", "ano_pib",
        "_silver_ts",
    ]].dropna(subset=["codigo_ibge"])

    out.to_sql("municipios_clean", engine, schema="silver", if_exists="replace",
               index=False, method="multi", chunksize=5000)
    return len(out)


# ─── Orquestrador ─────────────────────────────────────────────────────────────

TRANSFORMS = [
    ("clientes_clean",             _transform_clientes),
    ("clientes_sinteticos_clean",  _transform_clientes_sinteticos),
    ("contas_clean",               _transform_contas),
    ("transacoes_clean",           _transform_transacoes),
    ("agencias_clean",             _transform_agencias),
    ("colaboradores_clean",        _transform_colaboradores),
    ("propostas_clean",            _transform_propostas),
    ("ipca_clean",                 _transform_ipca),
    ("selic_clean",                _transform_selic),
    ("municipios_clean",           _transform_municipios),
]


def transformar_silver(engine=None) -> dict:
    if engine is None:
        engine = get_engine()
    resultados = {}
    for nome, fn in TRANSFORMS:
        n = fn(engine)
        resultados[nome] = n
        print(f"  silver.{nome}: {n:,} linhas")
    return resultados
