"""
BanVic 360° — Projecao de Series Historicas (Fase 6)
=====================================================
Estende os datasets externos ate 2026 usando CAGR e tendencia linear.

Series projetadas:
  IPCA mensal         -> 2026 (extende dados reais ate 2025)
  Selic diaria        -> 2025-2026 (extende dados reais ate 2024)
  CDI diario          -> 2025-2026
  Populacao municipal -> 2023-2026 (extende Censo 2022, taxa IBGE 0.7% a.a.)
  PIB municipal       -> 2022-2026 (extende dado de 2021, CAGR regional)

Saida: external_data/projecoes/
  ipca_projetado.csv
  selic_projetada.csv
  cdi_projetado.csv
  populacao_projetada.csv
  pib_projetado.csv

Uso:
    python scripts/projetar_series_historicas.py
    python scripts/projetar_series_historicas.py --serie ipca
    python scripts/projetar_series_historicas.py --serie tudo
"""

import argparse
import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
EXT          = PROJECT_ROOT / "external_data"
OUT          = PROJECT_ROOT / "external_data" / "projecoes"

# ─── Cenarios macroeconomicos BanVic (ficcionais, coerentes com 2023-2026) ────

# Selic meta por ano (% a.a.) — cenario BanVic
SELIC_META_ANUAL = {
    2025: 14.75,  # alta continuada vs 2024
    2026: 12.50,  # inicio de ciclo de queda
}

# IPCA esperado por ano (% a.a.) — cenario BanVic
IPCA_META_ANUAL = {
    2026: 4.5,    # proximo ao teto da meta
}

# CAGR de PIB por regiao (% a.a.) — baseado em historico 2018-2021
CAGR_PIB_REGIAO = {
    "Norte":        0.065,
    "Nordeste":     0.055,
    "Centro-Oeste": 0.080,
    "Sudeste":      0.048,
    "Sul":          0.058,
}

# Taxa de crescimento populacional anual por regiao (IBGE estimativas)
CRESCIMENTO_POP_REGIAO = {
    "Norte":        0.010,
    "Nordeste":     0.004,
    "Centro-Oeste": 0.012,
    "Sudeste":      0.005,
    "Sul":          0.006,
}

# Mapa UF -> regiao
UF_REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}


def dias_uteis_mes(ano: int, mes: int) -> int:
    """Estimativa de dias uteis num mes (excluindo sabados e domingos)."""
    d = date(ano, mes, 1)
    count = 0
    while d.month == mes:
        if d.weekday() < 5:
            count += 1
        d += timedelta(days=1)
    return count


# ─── 1. IPCA projetado ────────────────────────────────────────────────────────

def projetar_ipca() -> Path:
    """Projeta IPCA mensal para 2026 usando taxa media dos ultimos 3 anos."""
    dados = []
    with open(EXT / "macroeconomia" / "ipca.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dados.append(row)

    # Calcular variacao media mensal dos ultimos 36 meses (2022-2024)
    ultimos_36 = [r for r in dados if int(r["ano"]) >= 2022]
    taxas_mens = [float(r["no_mes"]) for r in ultimos_36 if r["no_mes"]]
    media_mens = sum(taxas_mens) / len(taxas_mens) if taxas_mens else 0.37

    # Indice base = ultimo indice disponivel
    ultimo_indice = float(dados[-1]["indice"])
    ultimo_acum12 = float(dados[-1]["acumulado_12m"])
    ultimo_ano_mes = (int(dados[-1]["ano"]), int(dados[-1]["mes_num"]))

    projecoes = []
    MESES_PT = ["", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

    # Projetar 2026 (12 meses)
    ipca_alvo_aa = IPCA_META_ANUAL[2026]  # 4.5% a.a.
    # Distribuir sazonalmente (jan fraco, dez forte)
    sazonal = {
        1: 0.55, 2: 0.65, 3: 0.72, 4: 0.43, 5: 0.38, 6: 0.20,
        7: 0.30, 8: 0.35, 9: 0.44, 10: 0.52, 11: 0.39, 12: 0.52
    }
    # Normalizar para que a soma anual bata com ipca_alvo_aa
    soma_sazon = sum(sazonal.values())
    fator_norm = ipca_alvo_aa / 12 / (soma_sazon / 12)

    acum3 = []
    indice_atual = ultimo_indice

    for mes_num in range(1, 13):
        ano = 2026
        variacao = round(sazonal[mes_num] * fator_norm, 2)
        indice_atual = round(indice_atual * (1 + variacao / 100), 2)
        acum3.append(variacao)
        if len(acum3) > 3:
            acum3.pop(0)
        acum3m = round(sum(acum3), 2)
        # acum_ano = soma das variacoes de jan ao mes
        acum_ano = round(sum(
            sazonal[m] * fator_norm for m in range(1, mes_num + 1)
        ), 2)
        acum12 = round(last12(dados, projecoes, ano, mes_num, variacao), 2)

        projecoes.append({
            "data":          f"{ano}-{mes_num:02d}-01",
            "ano":           ano,
            "mes":           MESES_PT[mes_num],
            "mes_num":       mes_num,
            "indice":        indice_atual,
            "no_mes":        variacao,
            "acumulado_3m":  acum3m,
            "acumulado_12m": acum12,
            "acumulado_ano": acum_ano,
            "tipo":          "PROJECAO",
        })

    OUT.mkdir(parents=True, exist_ok=True)
    # Gravar com dados reais + projecoes
    out_file = OUT / "ipca_projetado.csv"
    campos = ["data", "ano", "mes", "mes_num", "indice", "no_mes",
              "acumulado_3m", "acumulado_12m", "acumulado_ano", "tipo"]

    # Reescrever dados reais com tipo=REAL
    reais_out = []
    for r in dados:
        reais_out.append({
            "data": r["data"], "ano": r["ano"], "mes": r["mes"],
            "mes_num": r["mes_num"], "indice": r["indice"],
            "no_mes": r["no_mes"], "acumulado_3m": r["acumulado_3m"],
            "acumulado_12m": r["acumulado_12m"],
            "acumulado_ano": r["acumulado_ano"], "tipo": "REAL",
        })

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(reais_out + projecoes)

    print(f"OK ipca_projetado.csv -> {len(reais_out)} reais + {len(projecoes)} projetados (2026)")
    return out_file


def last12(reais, proj, ano, mes, var_atual):
    """Calcula acumulado 12 meses incluindo historico real."""
    todos = [(int(r["ano"]), int(r["mes_num"]), float(r["no_mes"])) for r in reais]
    for p in proj:
        todos.append((int(p["ano"]), int(p["mes_num"]), float(p["no_mes"])))
    todos.append((ano, mes, var_atual))
    todos.sort()
    idx = next(i for i, t in enumerate(todos) if t[0] == ano and t[1] == mes)
    ultimos = todos[max(0, idx - 11): idx + 1]
    # Acumular de forma composta
    fator = 1.0
    for _, _, v in ultimos:
        fator *= (1 + v / 100)
    return round((fator - 1) * 100, 2)


# ─── 2. Selic projetada ───────────────────────────────────────────────────────

def projetar_selic() -> Path:
    """Projeta taxa Selic diaria para 2025 e 2026."""
    rng = random.Random(42)

    dados = []
    with open(EXT / "macroeconomia" / "selic.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dados.append(row)

    ultimo_real = date.fromisoformat(dados[-1]["data"])
    ultima_taxa = float(dados[-1]["taxa_selic"])

    projecoes = []

    for ano in [2025, 2026]:
        meta_aa = SELIC_META_ANUAL[ano]
        taxa_dia_alvo = meta_aa / 100 / 252  # taxa over diaria

        d = date(ano, 1, 1)
        fim = date(ano, 12, 31)
        while d <= fim:
            if d > ultimo_real and d.weekday() < 5:
                # Suavizar transicao: interpolar entre ultima taxa e alvo
                if ano == 2025:
                    frac = (d - date(2025, 1, 1)).days / 365
                    taxa = ultima_taxa + (taxa_dia_alvo - ultima_taxa) * frac
                else:
                    frac_25 = SELIC_META_ANUAL[2025] / 100 / 252
                    frac = (d - date(2026, 1, 1)).days / 365
                    taxa = frac_25 + (taxa_dia_alvo - frac_25) * frac
                # Pequeno ruido diario
                taxa += rng.gauss(0, 0.0000005)
                projecoes.append({
                    "data":       d.isoformat(),
                    "taxa_selic": round(max(0.0001, taxa), 6),
                    "tipo":       "PROJECAO",
                })
            d += timedelta(days=1)

    out_file = OUT / "selic_projetada.csv"
    reais_out = [{"data": r["data"], "taxa_selic": r["taxa_selic"], "tipo": "REAL"} for r in dados]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "taxa_selic", "tipo"])
        writer.writeheader()
        writer.writerows(reais_out + projecoes)

    print(f"OK selic_projetada.csv -> {len(reais_out)} reais + {len(projecoes)} projetados (2025-2026)")
    return out_file


# ─── 3. CDI projetado ─────────────────────────────────────────────────────────

def projetar_cdi() -> Path:
    """CDI segue Selic com spread minimo (~0.01% a.a. menor)."""
    rng = random.Random(43)

    dados = []
    with open(EXT / "macroeconomia" / "cdi.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dados.append(row)

    ultimo_real = date.fromisoformat(dados[-1]["data"])

    projecoes = []
    for ano in [2025, 2026]:
        meta_aa = SELIC_META_ANUAL[ano] - 0.10  # CDI = Selic - 0.1% a.a.
        taxa_dia_alvo = meta_aa / 100 / 252

        ultima_taxa = float(dados[-1]["taxa_cdi"])

        d = date(ano, 1, 1)
        fim = date(ano, 12, 31)
        while d <= fim:
            if d > ultimo_real and d.weekday() < 5:
                if ano == 2025:
                    frac = (d - date(2025, 1, 1)).days / 365
                    taxa = ultima_taxa + (taxa_dia_alvo - ultima_taxa) * frac
                else:
                    frac_25 = (SELIC_META_ANUAL[2025] - 0.10) / 100 / 252
                    frac = (d - date(2026, 1, 1)).days / 365
                    taxa = frac_25 + (taxa_dia_alvo - frac_25) * frac
                taxa += rng.gauss(0, 0.0000003)
                projecoes.append({
                    "data":     d.isoformat(),
                    "taxa_cdi": round(max(0.0001, taxa), 6),
                    "tipo":     "PROJECAO",
                })
            d += timedelta(days=1)

    out_file = OUT / "cdi_projetado.csv"
    reais_out = [{"data": r["data"], "taxa_cdi": r["taxa_cdi"], "tipo": "REAL"} for r in dados]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "taxa_cdi", "tipo"])
        writer.writeheader()
        writer.writerows(reais_out + projecoes)

    print(f"OK cdi_projetado.csv -> {len(reais_out)} reais + {len(projecoes)} projetados (2025-2026)")
    return out_file


# ─── 4. Populacao municipal projetada ─────────────────────────────────────────

def projetar_populacao() -> Path:
    """Projeta populacao municipal de 2023 a 2026 a partir do Censo 2022."""
    municipios_raw = []
    with open(EXT / "geografia" / "municipios.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            municipios_raw.append(row)

    # Mapa codigo_ibge -> uf (para determinar regiao)
    uf_mapa = {}
    for m in municipios_raw:
        cod = m.get("codigo_ibge") or m.get("id", "")
        uf  = m.get("uf", m.get("sigla", "SP"))
        uf_mapa[str(cod)] = uf

    dados_pop = []
    with open(EXT / "geografia" / "populacao.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dados_pop.append(row)

    rows_out = []
    # Reescrever reais com tipo=REAL
    for r in dados_pop:
        rows_out.append({
            "codigo_ibge":  r["codigo_ibge"],
            "municipio":    r["municipio"],
            "uf":           uf_mapa.get(str(r["codigo_ibge"]), ""),
            "ano":          r["ano"],
            "populacao":    r["populacao"],
            "tipo":         "REAL",
        })

    # Projetar 2023-2026 para cada municipio
    for r in dados_pop:
        cod = str(r["codigo_ibge"])
        uf  = uf_mapa.get(cod, "SP")
        regiao = UF_REGIAO.get(uf, "Sudeste")
        taxa = CRESCIMENTO_POP_REGIAO[regiao]

        pop_base = int(r["populacao"])
        ano_base = int(r["ano"])  # 2022

        for ano in [2023, 2024, 2025, 2026]:
            anos_diff = ano - ano_base
            pop = round(pop_base * (1 + taxa) ** anos_diff)
            rows_out.append({
                "codigo_ibge":  r["codigo_ibge"],
                "municipio":    r["municipio"],
                "uf":           uf,
                "ano":          ano,
                "populacao":    pop,
                "tipo":         "PROJECAO",
            })

    out_file = OUT / "populacao_projetada.csv"
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["codigo_ibge", "municipio", "uf", "ano", "populacao", "tipo"])
        writer.writeheader()
        writer.writerows(rows_out)

    reais = sum(1 for r in rows_out if r["tipo"] == "REAL")
    proj  = sum(1 for r in rows_out if r["tipo"] == "PROJECAO")
    print(f"OK populacao_projetada.csv -> {reais:,} reais + {proj:,} projetados (2023-2026, {len(dados_pop):,} municipios)")
    return out_file


# ─── 5. PIB municipal projetado ───────────────────────────────────────────────

def projetar_pib() -> Path:
    """Projeta PIB municipal de 2022 a 2026 a partir do dado de 2021."""
    municipios_raw = []
    with open(EXT / "geografia" / "municipios.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            municipios_raw.append(row)

    uf_mapa = {}
    for m in municipios_raw:
        cod = m.get("codigo_ibge") or m.get("id", "")
        uf  = m.get("uf", m.get("sigla", "SP"))
        uf_mapa[str(cod)] = uf

    dados_pib = []
    with open(EXT / "geografia" / "pib_municipal.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dados_pib.append(row)

    rows_out = []
    # Reais
    for r in dados_pib:
        rows_out.append({
            "codigo_ibge":    r["codigo_ibge"],
            "municipio":      r["municipio"],
            "uf":             uf_mapa.get(str(r["codigo_ibge"]), ""),
            "ano":            r["ano"],
            "pib_total":      r["pib_total"],
            "pib_per_capita": r["pib_per_capita"],
            "tipo":           "REAL",
        })

    # Projecoes 2022-2026
    for r in dados_pib:
        cod = str(r["codigo_ibge"])
        uf  = uf_mapa.get(cod, "SP")
        regiao = UF_REGIAO.get(uf, "Sudeste")
        cagr = CAGR_PIB_REGIAO[regiao]

        pib_base    = float(r["pib_total"])
        ppc_base    = float(r["pib_per_capita"])
        ano_base    = int(r["ano"])  # 2021

        for ano in [2022, 2023, 2024, 2025, 2026]:
            anos_diff = ano - ano_base
            pib   = round(pib_base * (1 + cagr) ** anos_diff)
            # PIB per capita: crescimento = CAGR_PIB - CAGR_POP
            cagr_pop = CRESCIMENTO_POP_REGIAO[regiao]
            ppc   = round(ppc_base * (1 + cagr - cagr_pop) ** anos_diff, 2)
            rows_out.append({
                "codigo_ibge":    r["codigo_ibge"],
                "municipio":      r["municipio"],
                "uf":             uf,
                "ano":            ano,
                "pib_total":      pib,
                "pib_per_capita": ppc,
                "tipo":           "PROJECAO",
            })

    out_file = OUT / "pib_projetado.csv"
    campos = ["codigo_ibge", "municipio", "uf", "ano", "pib_total", "pib_per_capita", "tipo"]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(rows_out)

    reais = sum(1 for r in rows_out if r["tipo"] == "REAL")
    proj  = sum(1 for r in rows_out if r["tipo"] == "PROJECAO")
    print(f"OK pib_projetado.csv -> {reais:,} reais + {proj:,} projetados (2022-2026, {len(dados_pib):,} municipios)")
    return out_file


# ─── Entry point ──────────────────────────────────────────────────────────────

SERIES = {
    "ipca":       projetar_ipca,
    "selic":      projetar_selic,
    "cdi":        projetar_cdi,
    "populacao":  projetar_populacao,
    "pib":        projetar_pib,
}


def main():
    parser = argparse.ArgumentParser(description="BanVic -- Projecao de Series Historicas (Fase 6)")
    parser.add_argument("--serie", choices=list(SERIES) + ["tudo"], default="tudo")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    if args.serie == "tudo":
        for nome, fn in SERIES.items():
            print(f"\n[{nome.upper()}]")
            fn()
    else:
        SERIES[args.serie]()

    print(f"\nArquivos em: {OUT}")


if __name__ == "__main__":
    main()
