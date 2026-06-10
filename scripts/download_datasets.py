"""
BanVic - Script de Download de Datasets Externos
================================================
Baixa automaticamente os 14 datasets externos do projeto BanVic:
  1.  Dólar PTAX          ->dolar_ptax.csv            (Banco Central do Brasil)
  2.  Taxa Selic          ->selic.csv                 (Banco Central do Brasil)
  3.  IPCA                ->ipca.csv                  (Banco Central do Brasil)
  4.  Feriados Nacionais  ->feriados.csv              (BrasilAPI)
  5.  Municípios          ->municipios.csv            (IBGE API v1)
  6.  População           ->populacao.csv             (IBGE API v3 - Censo 2022)
  7.  PIB Municipal       ->pib_municipal.csv         (IBGE API v3 - 2021)
  8.  CDI Diário          ->cdi.csv                   (Banco Central do Brasil SGS-12)
  9.  IGP-M Mensal        ->igpm.csv                  (Banco Central do Brasil SGS-189)
  10. Taxa Desemprego     ->desemprego.csv             (BCB/PNAD Contínua SGS-28763)
  11. Euro PTAX           ->euro_ptax.csv             (Banco Central do Brasil PTAX)
  12. Renda Municipal     ->renda_municipal.csv        (IBGE Censo 2022)
  13. Escolaridade        ->escolaridade_municipal.csv (IBGE Censo 2022)
  14. Clima Histórico     ->clima_historico.csv        (Open-Meteo Archive — 100 cidades)

Uso:
    python download_datasets.py
    python download_datasets.py --dataset cdi
    python download_datasets.py --dataset clima --ano-inicio 2020 --ano-fim 2024
    python download_datasets.py --ano-inicio 2022 --ano-fim 2025
"""

import argparse
import csv
import gzip
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

import importlib.util
USE_REQUESTS = importlib.util.find_spec("requests") is not None

# Raiz do projeto (pasta acima de scripts/)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
OUTPUT_DIR = PROJECT_ROOT  # base para montar caminhos

# Subpastas por tema
_MACRO = os.path.join(PROJECT_ROOT, "external_data", "macroeconomia")
_GEO   = os.path.join(PROJECT_ROOT, "external_data", "geografia")
_CAL   = os.path.join(PROJECT_ROOT, "external_data", "calendario")
_CLIMA = os.path.join(PROJECT_ROOT, "external_data", "clima")

DIRS = {
    "ptax":         _MACRO,
    "selic":        _MACRO,
    "ipca":         _MACRO,
    "cdi":          _MACRO,
    "igpm":         _MACRO,
    "desemprego":   _MACRO,
    "euro":         _MACRO,
    "feriados":     _CAL,
    "municipios":   _GEO,
    "populacao":    _GEO,
    "pib":          _GEO,
    "renda":        _GEO,
    "escolaridade": _GEO,
    "clima":        _CLIMA,
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def fetch(url: str, timeout: int = 120) -> dict | list:
    if USE_REQUESTS:
        import requests as req
        headers = {"User-Agent": "BanVic-ETL/1.0", "Accept": "application/json"}
        r = req.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()

    req_obj = urllib.request.Request(url, headers={
        "User-Agent": "BanVic-ETL/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req_obj, timeout=timeout) as resp:
        raw = resp.read()
        if resp.info().get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))


def write_csv(path: str, fieldnames: list, rows: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def out(name: str, dataset_key: str = None) -> str:
    if dataset_key and dataset_key in DIRS:
        return os.path.join(DIRS[dataset_key], name)
    return os.path.join(OUTPUT_DIR, name)


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ─── dataset 1: Dólar PTAX ────────────────────────────────────────────────────

def download_ptax(ano_inicio: int = 2020, ano_fim: int = 2024) -> str:
    log("PTAX: consultando Banco Central do Brasil...")
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarPeriodo(dataInicial=@i,dataFinalCotacao=@f)"
        f"?@i='01-01-{ano_inicio}'&@f='12-31-{ano_fim}'"
        "&$top=5000&$format=json&$select=cotacaoCompra,cotacaoVenda,dataHoraCotacao"
    )
    data = fetch(url)["value"]
    log(f"PTAX: {len(data)} cotações recebidas")

    daily: dict = {}
    for r in data:
        dt = datetime.fromisoformat(r["dataHoraCotacao"].replace("Z", ""))
        day = dt.strftime("%Y-%m-%d")
        daily[day] = {
            "data": day,
            "cotacao_compra": round(r["cotacaoCompra"], 4),
            "cotacao_venda": round(r["cotacaoVenda"], 4),
            "cotacao_media": round((r["cotacaoCompra"] + r["cotacaoVenda"]) / 2, 4),
        }

    rows = sorted(daily.values(), key=lambda x: x["data"])
    path = out("dolar_ptax.csv", "ptax")
    write_csv(path, ["data", "cotacao_compra", "cotacao_venda", "cotacao_media"], rows)
    log(f"PTAX: {len(rows)} dias ->{path}")
    return path


# ─── dataset 2: Taxa Selic ────────────────────────────────────────────────────

def download_selic(ano_inicio: int = 2020, ano_fim: int = 2024) -> str:
    log("Selic: consultando Banco Central do Brasil...")
    di = f"01/01/{ano_inicio}"
    df = f"31/12/{ano_fim}"
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={di}&dataFinal={df}"
    data = fetch(url)
    log(f"Selic: {len(data)} registros recebidos")

    rows = []
    for r in data:
        dt = datetime.strptime(r["data"], "%d/%m/%Y")
        val = r["valor"].replace(",", ".") if r["valor"] else None
        rows.append({
            "data": dt.strftime("%Y-%m-%d"),
            "taxa_selic": float(val) if val else None,
        })

    path = out("selic.csv", "selic")
    write_csv(path, ["data", "taxa_selic"], rows)
    log(f"Selic: {len(rows)} dias ->{path}")
    return path


# ─── dataset 3: Feriados Nacionais ────────────────────────────────────────────

def download_feriados(ano_inicio: int = 2020, ano_fim: int = 2025) -> str:
    log("Feriados: consultando BrasilAPI...")
    all_rows = []
    for year in range(ano_inicio, ano_fim + 1):
        url = f"https://brasilapi.com.br/api/feriados/v1/{year}"
        try:
            data = fetch(url, timeout=30)
            for f in data:
                all_rows.append({
                    "data": f["date"],
                    "nome_feriado": f["name"],
                    "tipo": f.get("type", "nacional"),
                })
            log(f"  {year}: {len(data)} feriados")
        except Exception as e:
            log(f"  {year}: ERRO - {e}")

    all_rows.sort(key=lambda x: x["data"])
    path = out("feriados.csv", "feriados")
    write_csv(path, ["data", "nome_feriado", "tipo"], all_rows)
    log(f"Feriados: {len(all_rows)} registros ->{path}")
    return path


# ─── dataset 4: Municípios ────────────────────────────────────────────────────

REGIOES = {"N": "Norte", "NE": "Nordeste", "SE": "Sudeste", "S": "Sul", "CO": "Centro-Oeste"}


def download_municipios() -> str:
    log("Municípios: consultando IBGE API v1...")
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
    municipios = fetch(url)
    log(f"Municípios: {len(municipios)} recebidos")

    rows = []
    for m in municipios:
        if m.get("microrregiao"):
            uf = m["microrregiao"]["mesorregiao"]["UF"]
        else:
            uf = m["regiao-imediata"]["regiao-intermediaria"]["UF"]
        reg = uf["regiao"]["sigla"]
        rows.append({
            "codigo_ibge": m["id"],
            "municipio": m["nome"],
            "uf": uf["sigla"],
            "uf_nome": uf["nome"],
            "regiao": REGIOES.get(reg, reg),
            "regiao_sigla": reg,
        })

    rows.sort(key=lambda x: (x["uf"], x["municipio"]))
    path = out("municipios.csv", "municipios")
    write_csv(path, ["codigo_ibge", "municipio", "uf", "uf_nome", "regiao", "regiao_sigla"], rows)
    log(f"Municípios: {len(rows)} ->{path}")
    return path


# ─── dataset 5: População Municipal ──────────────────────────────────────────

def download_populacao() -> str:
    log("População: consultando IBGE API v3 (Censo 2022)...")
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/9606/periodos/2022/variaveis/93"
        "?localidades=N6[all]&classificacao=2[6794]|86[95251]|287[100362]"
    )
    data = fetch(url, timeout=300)
    rows = []
    for resultado in data[0]["resultados"]:
        for serie in resultado["series"]:
            cod = serie["localidade"]["id"]
            nome = serie["localidade"]["nome"]
            val = serie["serie"].get("2022", "")
            if val and val not in ["-", "...", "X", ""]:
                try:
                    rows.append({
                        "codigo_ibge": cod,
                        "municipio": nome,
                        "ano": 2022,
                        "populacao": int(val.replace(" ", "")),
                    })
                except ValueError:
                    pass

    rows.sort(key=lambda x: int(x["codigo_ibge"]))
    path = out("populacao.csv", "populacao")
    write_csv(path, ["codigo_ibge", "municipio", "ano", "populacao"], rows)
    log(f"População: {len(rows)} municípios ->{path}")
    return path


# ─── dataset 6: PIB Municipal ─────────────────────────────────────────────────

def download_pib(ano: int = 2021) -> str:
    log(f"PIB Municipal: consultando IBGE API v3 ({ano})...")
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/5938/periodos/{ano}/variaveis/37"
        "?localidades=N6[all]"
    )
    data = fetch(url, timeout=300)

    pib_rows: dict = {}
    for resultado in data[0]["resultados"]:
        for serie in resultado["series"]:
            cod = serie["localidade"]["id"]
            nome = serie["localidade"]["nome"]
            val = serie["serie"].get(str(ano), "")
            if val and val not in ["-", "...", "X", ""]:
                try:
                    pib_mil = int(val.replace(" ", ""))
                    pib_rows[cod] = {
                        "codigo_ibge": cod,
                        "municipio": nome,
                        "ano": ano,
                        "pib_total": pib_mil * 1000,
                    }
                except ValueError:
                    pass

    # Calcular PIB per capita a partir da população do Censo 2022
    pop_path = out("populacao.csv", "populacao")
    pop_data: dict = {}
    if os.path.exists(pop_path):
        with open(pop_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pop_data[row["codigo_ibge"]] = int(row["populacao"])

    rows = []
    for cod, d in pib_rows.items():
        pop = pop_data.get(str(cod), 0)
        rows.append({
            "codigo_ibge": d["codigo_ibge"],
            "municipio": d["municipio"],
            "ano": d["ano"],
            "pib_total": d["pib_total"],
            "pib_per_capita": round(d["pib_total"] / pop, 2) if pop > 0 else None,
        })

    rows.sort(key=lambda x: int(x["codigo_ibge"]))
    path = out("pib_municipal.csv", "pib")
    write_csv(path, ["codigo_ibge", "municipio", "ano", "pib_total", "pib_per_capita"], rows)
    log(f"PIB Municipal: {len(rows)} municípios ->{path}")
    return path


# ─── dataset 7: IPCA ─────────────────────────────────────────────────────────

MESES_PT = {1:"JAN",2:"FEV",3:"MAR",4:"ABR",5:"MAI",6:"JUN",
            7:"JUL",8:"AGO",9:"SET",10:"OUT",11:"NOV",12:"DEZ"}

BASE_INDICE_IPCA_2010_01 = 3040.22  # IBGE, índice acumulado base dez/1993=100


def _fetch_sgs(serie: int, data_ini: str, data_fim: str) -> list:
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
           f"?formato=json&dataInicial={data_ini}&dataFinal={data_fim}")
    return fetch(url, timeout=60)


def _parse_val(v) -> float | None:
    if not v or str(v).strip() in ["-", "", "null"]:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def _sgs_to_dict(series: list) -> dict:
    d = {}
    for r in series:
        dt = datetime.strptime(r["data"], "%d/%m/%Y")
        d[dt.strftime("%Y-%m")] = _parse_val(r["valor"])
    return d


def download_ipca(ano_inicio: int = 2010, ano_fim: int = 2025) -> str:
    log("IPCA: consultando Banco Central do Brasil (SGS)...")
    di = f"01/01/{ano_inicio}"
    df = f"31/12/{ano_fim}"

    mensal = _sgs_to_dict(_fetch_sgs(433, di, df))   # variação mensal %
    m3     = _sgs_to_dict(_fetch_sgs(4449, di, df))  # acumulado 3 meses
    m12    = _sgs_to_dict(_fetch_sgs(13522, di, df)) # acumulado 12 meses

    log(f"  Mensal: {len(mensal)} | 3m: {len(m3)} | 12m: {len(m12)} registros")

    # Calcular índice acumulado a partir da base jan/ano_inicio
    indice = BASE_INDICE_IPCA_2010_01 if ano_inicio == 2010 else None
    rows = []
    for chave in sorted(mensal.keys()):
        y, m = int(chave[:4]), int(chave[5:])
        var = mensal.get(chave)

        # Calcular acumulado no ano (produto dos fatores mensais)
        acum_ano = 1.0
        for mm in range(1, m + 1):
            v = mensal.get(f"{y}-{mm:02d}")
            if v is not None:
                acum_ano *= (1 + v / 100)
        acum_ano_pct = round((acum_ano - 1) * 100, 2)

        # Avançar índice
        if indice is not None and var is not None:
            indice = round(indice * (1 + var / 100), 2)

        rows.append({
            "data": f"{y}-{m:02d}-01",
            "ano": y,
            "mes": MESES_PT[m],
            "mes_num": m,
            "indice": indice,
            "no_mes": var,
            "acumulado_3m": m3.get(chave),
            "acumulado_12m": m12.get(chave),
            "acumulado_ano": acum_ano_pct,
        })

    path = out("ipca.csv", "ipca")
    fields = ["data","ano","mes","mes_num","indice","no_mes","acumulado_3m","acumulado_12m","acumulado_ano"]
    write_csv(path, fields, rows)
    log(f"IPCA: {len(rows)} meses ({rows[0]['data']} ->{rows[-1]['data']}) ->{path}")
    return path


# ─── dataset 8: CDI Diário ───────────────────────────────────────────────────

def download_cdi(ano_inicio: int = 2020, ano_fim: int = 2024) -> str:
    log("CDI: consultando Banco Central do Brasil (SGS série 12)...")
    di = f"01/01/{ano_inicio}"
    df = f"31/12/{ano_fim}"
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
           f"?formato=json&dataInicial={di}&dataFinal={df}")
    data = fetch(url)
    log(f"CDI: {len(data)} registros recebidos")

    rows = []
    for r in data:
        dt = datetime.strptime(r["data"], "%d/%m/%Y")
        val = r["valor"].replace(",", ".") if r["valor"] else None
        rows.append({
            "data":     dt.strftime("%Y-%m-%d"),
            "taxa_cdi": float(val) if val else None,
        })

    path = out("cdi.csv", "cdi")
    write_csv(path, ["data", "taxa_cdi"], rows)
    log(f"CDI: {len(rows)} dias ->{path}")
    return path


# ─── dataset 9: IGP-M Mensal ─────────────────────────────────────────────────

def download_igpm(ano_inicio: int = 2010, ano_fim: int = 2025) -> str:
    log("IGP-M: consultando Banco Central do Brasil (SGS)...")
    di = f"01/01/{ano_inicio}"
    df = f"31/12/{ano_fim}"

    mensal = _sgs_to_dict(_fetch_sgs(189,  di, df))   # variação mensal %
    m12    = _sgs_to_dict(_fetch_sgs(4175, di, df))   # acumulado 12m %
    log(f"  IGP-M mensal: {len(mensal)} | 12m: {len(m12)}")

    rows = []
    for chave in sorted(mensal.keys()):
        y, m = int(chave[:4]), int(chave[5:])
        rows.append({
            "data":             f"{y}-{m:02d}-01",
            "ano":              y,
            "mes":              MESES_PT[m],
            "mes_num":          m,
            "variacao_mensal":  mensal.get(chave),
            "acumulado_12m":    m12.get(chave),
        })

    path = out("igpm.csv", "igpm")
    write_csv(path, ["data", "ano", "mes", "mes_num", "variacao_mensal", "acumulado_12m"], rows)
    log(f"IGP-M: {len(rows)} meses ->{path}")
    return path


# ─── dataset 10: Taxa de Desemprego (PNAD Contínua) ──────────────────────────

def download_desemprego(ano_inicio: int = 2015, ano_fim: int = 2024) -> str:
    log("Desemprego: consultando BCB (SGS série 24369 — PNAD Contínua taxa mensal %)...")
    di = f"01/01/{ano_inicio}"
    df = f"31/12/{ano_fim}"
    url = (f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.24369/dados"
           f"?formato=json&dataInicial={di}&dataFinal={df}")
    data = fetch(url)
    log(f"Desemprego: {len(data)} registros recebidos")

    rows = []
    for r in data:
        dt  = datetime.strptime(r["data"], "%d/%m/%Y")
        val = r["valor"].replace(",", ".") if r["valor"] else None
        rows.append({
            "data":                 dt.strftime("%Y-%m-%d"),
            "ano":                  dt.year,
            "trimestre":            (dt.month - 1) // 3 + 1,
            "taxa_desemprego_pct":  float(val) if val else None,
        })

    path = out("desemprego.csv", "desemprego")
    write_csv(path, ["data", "ano", "trimestre", "taxa_desemprego_pct"], rows)
    log(f"Desemprego: {len(rows)} trimestres ->{path}")
    return path


# ─── dataset 11: Euro PTAX ───────────────────────────────────────────────────

def download_euro(ano_inicio: int = 2020, ano_fim: int = 2024) -> str:
    log("Euro PTAX: consultando Banco Central do Brasil...")
    url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoMoedaPeriodo(moeda=@m,dataInicial=@i,dataFinalCotacao=@f)"
        f"?@m='EUR'&@i='01-01-{ano_inicio}'&@f='12-31-{ano_fim}'"
        "&$top=10000&$format=json&$select=cotacaoCompra,cotacaoVenda,dataHoraCotacao"
    )
    data = fetch(url)["value"]
    log(f"Euro PTAX: {len(data)} cotações recebidas")

    daily: dict = {}
    for r in data:
        dt  = datetime.fromisoformat(r["dataHoraCotacao"].replace("Z", ""))
        day = dt.strftime("%Y-%m-%d")
        daily[day] = {
            "data":          day,
            "cotacao_compra": round(r["cotacaoCompra"], 4),
            "cotacao_venda":  round(r["cotacaoVenda"],  4),
            "cotacao_media":  round((r["cotacaoCompra"] + r["cotacaoVenda"]) / 2, 4),
        }

    rows = sorted(daily.values(), key=lambda x: x["data"])
    path = out("euro_ptax.csv", "euro")
    write_csv(path, ["data", "cotacao_compra", "cotacao_venda", "cotacao_media"], rows)
    log(f"Euro PTAX: {len(rows)} dias ->{path}")
    return path


# ─── dataset 12: Renda Municipal ─────────────────────────────────────────────

def download_renda() -> str:
    log("Renda Municipal: consultando IBGE API v3 (Censo 2022 — tabela 9605)...")
    # Tabela 9605: Domicílios Particulares Permanentes, Censo 2022
    # Variável 5933: Valor do rendimento nominal médio mensal per capita (R$)
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/9605/periodos/2022/variaveis/5933"
        "?localidades=N6[all]"
    )
    path = out("renda_municipal.csv", "renda")
    fields = ["codigo_ibge", "municipio", "ano", "renda_media_per_capita", "fonte"]

    try:
        data = fetch(url, timeout=300)
        rows = []
        for resultado in data[0]["resultados"]:
            for serie in resultado["series"]:
                cod  = serie["localidade"]["id"]
                nome = serie["localidade"]["nome"]
                val  = serie["serie"].get("2022", "")
                if val and val not in ["-", "...", "X", ""]:
                    try:
                        rows.append({
                            "codigo_ibge":          cod,
                            "municipio":            nome,
                            "ano":                  2022,
                            "renda_media_per_capita": float(val.replace(" ", "").replace(",", ".")),
                            "fonte":                "IBGE Censo 2022 — tabela 9605",
                        })
                    except ValueError:
                        pass
        rows.sort(key=lambda x: int(x["codigo_ibge"]))
        write_csv(path, fields, rows)
        log(f"Renda Municipal: {len(rows)} municípios ->{path}")
    except Exception as e:
        log(f"  AVISO — tabela 9605 falhou: {e}")
        log("  Fallback: estimativa via PIB per capita / 12 (proxy)...")
        pib_path = out("pib_municipal.csv", "pib")
        rows = []
        if os.path.exists(pib_path):
            with open(pib_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    ppc = row.get("pib_per_capita") or ""
                    rows.append({
                        "codigo_ibge":          row["codigo_ibge"],
                        "municipio":            row["municipio"],
                        "ano":                  int(row["ano"]),
                        "renda_media_per_capita": round(float(ppc) / 12, 2) if ppc else None,
                        "fonte":                "ESTIMATIVA — PIB per capita/12 (Censo 2022 indisponível via API)",
                    })
        write_csv(path, fields, rows)
        log(f"  Renda estimada: {len(rows)} municípios ->{path}")
    return path


# ─── dataset 13: Escolaridade Municipal ──────────────────────────────────────

def download_escolaridade() -> str:
    log("Escolaridade: consultando IBGE API v3 (Censo 2022 — tabela 9612)...")
    # Tabela 9612: Pessoas por nível de instrução, Censo 2022
    # Variável 93: Total de pessoas; classificação por nível de instrução
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/9612/periodos/2022/variaveis/93"
        "?localidades=N6[all]"
    )
    path = out("escolaridade_municipal.csv", "escolaridade")
    fields = ["codigo_ibge", "municipio", "ano", "total_pessoas_5anos_mais", "fonte"]

    try:
        data = fetch(url, timeout=300)
        totais: dict = {}
        for resultado in data[0]["resultados"]:
            for serie in resultado["series"]:
                cod  = serie["localidade"]["id"]
                nome = serie["localidade"]["nome"]
                val  = serie["serie"].get("2022", "")
                if not val or val in ["-", "...", "X", ""]:
                    continue
                try:
                    n = int(val.replace(" ", ""))
                    if cod not in totais:
                        totais[cod] = {"municipio": nome, "total": 0}
                    totais[cod]["total"] += n
                except ValueError:
                    pass

        rows = [
            {
                "codigo_ibge":            cod,
                "municipio":              d["municipio"],
                "ano":                    2022,
                "total_pessoas_5anos_mais": d["total"],
                "fonte":                  "IBGE Censo 2022 — tabela 9612",
            }
            for cod, d in sorted(totais.items(), key=lambda x: int(x[0]))
        ]
        write_csv(path, fields, rows)
        log(f"Escolaridade: {len(rows)} municípios ->{path}")
    except Exception as e:
        log(f"  AVISO — tabela 9612 falhou: {e}")
        log("  Fallback: placeholder com lista de municípios...")
        mun_path = out("municipios.csv", "municipios")
        rows = []
        if os.path.exists(mun_path):
            with open(mun_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    rows.append({
                        "codigo_ibge":            row["codigo_ibge"],
                        "municipio":              row["municipio"],
                        "ano":                    2022,
                        "total_pessoas_5anos_mais": None,
                        "fonte":                  "PENDENTE — Dado não disponível via API IBGE",
                    })
        write_csv(path, fields, rows)
        log(f"  Placeholder: {len(rows)} municípios ->{path}")
    return path


# ─── dataset 14: Clima Histórico (Open-Meteo — 100 cidades) ─────────────────

CIDADES_CLIMA = [
    # Norte (10)
    {"codigo_ibge": "1302603", "municipio": "Manaus",               "uf": "AM", "lat":  -3.1190, "lon": -60.0217},
    {"codigo_ibge": "1501402", "municipio": "Belém",                "uf": "PA", "lat":  -1.4558, "lon": -48.5044},
    {"codigo_ibge": "1100205", "municipio": "Porto Velho",          "uf": "RO", "lat":  -8.7612, "lon": -63.9044},
    {"codigo_ibge": "1600303", "municipio": "Macapá",               "uf": "AP", "lat":   0.0389, "lon": -51.0664},
    {"codigo_ibge": "1506807", "municipio": "Santarém",             "uf": "PA", "lat":  -2.4384, "lon": -54.7044},
    {"codigo_ibge": "1200401", "municipio": "Rio Branco",           "uf": "AC", "lat":  -9.9747, "lon": -67.8096},
    {"codigo_ibge": "1400100", "municipio": "Boa Vista",            "uf": "RR", "lat":   2.8235, "lon": -60.6758},
    {"codigo_ibge": "1721000", "municipio": "Palmas",               "uf": "TO", "lat": -10.2491, "lon": -48.3243},
    {"codigo_ibge": "1504208", "municipio": "Marabá",               "uf": "PA", "lat":  -5.3686, "lon": -49.1178},
    {"codigo_ibge": "1502400", "municipio": "Ananindeua",           "uf": "PA", "lat":  -1.3654, "lon": -48.3726},
    # Nordeste (25)
    {"codigo_ibge": "2927408", "municipio": "Salvador",             "uf": "BA", "lat": -12.9714, "lon": -38.5014},
    {"codigo_ibge": "2304400", "municipio": "Fortaleza",            "uf": "CE", "lat":  -3.7172, "lon": -38.5434},
    {"codigo_ibge": "2611606", "municipio": "Recife",               "uf": "PE", "lat":  -8.0539, "lon": -34.8811},
    {"codigo_ibge": "2111300", "municipio": "São Luís",             "uf": "MA", "lat":  -2.5307, "lon": -44.3068},
    {"codigo_ibge": "2704302", "municipio": "Maceió",               "uf": "AL", "lat":  -9.6658, "lon": -35.7350},
    {"codigo_ibge": "2408102", "municipio": "Natal",                "uf": "RN", "lat":  -5.7945, "lon": -35.2110},
    {"codigo_ibge": "2211001", "municipio": "Teresina",             "uf": "PI", "lat":  -5.0892, "lon": -42.8019},
    {"codigo_ibge": "2507507", "municipio": "João Pessoa",          "uf": "PB", "lat":  -7.1195, "lon": -34.8450},
    {"codigo_ibge": "2800308", "municipio": "Aracaju",              "uf": "SE", "lat": -10.9472, "lon": -37.0731},
    {"codigo_ibge": "2910800", "municipio": "Feira de Santana",     "uf": "BA", "lat": -12.2664, "lon": -38.9663},
    {"codigo_ibge": "2304659", "municipio": "Caucaia",              "uf": "CE", "lat":  -3.7360, "lon": -38.6529},
    {"codigo_ibge": "2516201", "municipio": "Campina Grande",       "uf": "PB", "lat":  -7.2306, "lon": -35.8811},
    {"codigo_ibge": "2604106", "municipio": "Caruaru",              "uf": "PE", "lat":  -8.2840, "lon": -35.9762},
    {"codigo_ibge": "2933307", "municipio": "Vitória da Conquista", "uf": "BA", "lat": -14.8661, "lon": -40.8444},
    {"codigo_ibge": "2408003", "municipio": "Mossoró",              "uf": "RN", "lat":  -5.1878, "lon": -37.3438},
    {"codigo_ibge": "2318804", "municipio": "Juazeiro do Norte",    "uf": "CE", "lat":  -7.2129, "lon": -39.3157},
    {"codigo_ibge": "2111201", "municipio": "Imperatriz",           "uf": "MA", "lat":  -5.5261, "lon": -47.4914},
    {"codigo_ibge": "2316208", "municipio": "Sobral",               "uf": "CE", "lat":  -3.6861, "lon": -40.3508},
    {"codigo_ibge": "2611101", "municipio": "Petrolina",            "uf": "PE", "lat":  -9.3975, "lon": -40.5006},
    {"codigo_ibge": "2918407", "municipio": "Camaçari",             "uf": "BA", "lat": -12.6992, "lon": -38.3240},
    {"codigo_ibge": "2913606", "municipio": "Ilhéus",               "uf": "BA", "lat": -14.7890, "lon": -39.0470},
    {"codigo_ibge": "2701100", "municipio": "Arapiraca",            "uf": "AL", "lat":  -9.7528, "lon": -36.6611},
    {"codigo_ibge": "2207702", "municipio": "Parnaíba",             "uf": "PI", "lat":  -2.9062, "lon": -41.7740},
    {"codigo_ibge": "2903201", "municipio": "Barreiras",            "uf": "BA", "lat": -12.1530, "lon": -44.9940},
    {"codigo_ibge": "2606002", "municipio": "Garanhuns",            "uf": "PE", "lat":  -8.8892, "lon": -36.4962},
    # Centro-Oeste (10)
    {"codigo_ibge": "5300108", "municipio": "Brasília",             "uf": "DF", "lat": -15.7975, "lon": -47.8919},
    {"codigo_ibge": "5208707", "municipio": "Goiânia",              "uf": "GO", "lat": -16.6864, "lon": -49.2643},
    {"codigo_ibge": "5103403", "municipio": "Cuiabá",               "uf": "MT", "lat": -15.6014, "lon": -56.0979},
    {"codigo_ibge": "5002704", "municipio": "Campo Grande",         "uf": "MS", "lat": -20.4697, "lon": -54.6201},
    {"codigo_ibge": "5201405", "municipio": "Anápolis",             "uf": "GO", "lat": -16.3281, "lon": -48.9531},
    {"codigo_ibge": "5201108", "municipio": "Aparecida de Goiânia", "uf": "GO", "lat": -16.8229, "lon": -49.2449},
    {"codigo_ibge": "5108402", "municipio": "Várzea Grande",        "uf": "MT", "lat": -15.6467, "lon": -56.1367},
    {"codigo_ibge": "5003702", "municipio": "Dourados",             "uf": "MS", "lat": -22.2231, "lon": -54.8056},
    {"codigo_ibge": "5107602", "municipio": "Rondonópolis",         "uf": "MT", "lat": -16.4703, "lon": -54.6356},
    {"codigo_ibge": "5221858", "municipio": "Rio Verde",            "uf": "GO", "lat": -17.7983, "lon": -50.9239},
    # Sudeste (35)
    {"codigo_ibge": "3550308", "municipio": "São Paulo",            "uf": "SP", "lat": -23.5505, "lon": -46.6333},
    {"codigo_ibge": "3304557", "municipio": "Rio de Janeiro",       "uf": "RJ", "lat": -22.9068, "lon": -43.1729},
    {"codigo_ibge": "3106200", "municipio": "Belo Horizonte",       "uf": "MG", "lat": -19.9167, "lon": -43.9345},
    {"codigo_ibge": "3518800", "municipio": "Guarulhos",            "uf": "SP", "lat": -23.4628, "lon": -46.5333},
    {"codigo_ibge": "3509502", "municipio": "Campinas",             "uf": "SP", "lat": -22.9056, "lon": -47.0608},
    {"codigo_ibge": "3301702", "municipio": "São Gonçalo",          "uf": "RJ", "lat": -22.8268, "lon": -43.0546},
    {"codigo_ibge": "3301900", "municipio": "Duque de Caxias",      "uf": "RJ", "lat": -22.7864, "lon": -43.3117},
    {"codigo_ibge": "3303500", "municipio": "Nova Iguaçu",          "uf": "RJ", "lat": -22.7592, "lon": -43.4511},
    {"codigo_ibge": "3548708", "municipio": "São Bernardo do Campo","uf": "SP", "lat": -23.6939, "lon": -46.5650},
    {"codigo_ibge": "3547809", "municipio": "Santo André",          "uf": "SP", "lat": -23.6639, "lon": -46.5383},
    {"codigo_ibge": "3534401", "municipio": "Osasco",               "uf": "SP", "lat": -23.5324, "lon": -46.7920},
    {"codigo_ibge": "3543402", "municipio": "Ribeirão Preto",       "uf": "SP", "lat": -21.1704, "lon": -47.8103},
    {"codigo_ibge": "3549904", "municipio": "São José dos Campos",  "uf": "SP", "lat": -23.1794, "lon": -45.8869},
    {"codigo_ibge": "3552205", "municipio": "Sorocaba",             "uf": "SP", "lat": -23.5015, "lon": -47.4526},
    {"codigo_ibge": "3531902", "municipio": "Mogi das Cruzes",      "uf": "SP", "lat": -23.5228, "lon": -46.1859},
    {"codigo_ibge": "3136702", "municipio": "Juiz de Fora",         "uf": "MG", "lat": -21.7642, "lon": -43.3503},
    {"codigo_ibge": "3170206", "municipio": "Uberlândia",           "uf": "MG", "lat": -18.9186, "lon": -48.2772},
    {"codigo_ibge": "3205309", "municipio": "Vitória",              "uf": "ES", "lat": -20.3155, "lon": -40.3128},
    {"codigo_ibge": "3118601", "municipio": "Contagem",             "uf": "MG", "lat": -19.9317, "lon": -44.0536},
    {"codigo_ibge": "3205010", "municipio": "Serra",                "uf": "ES", "lat": -20.1286, "lon": -40.3073},
    {"codigo_ibge": "3205200", "municipio": "Vila Velha",           "uf": "ES", "lat": -20.3297, "lon": -40.2924},
    {"codigo_ibge": "3303302", "municipio": "Niterói",              "uf": "RJ", "lat": -22.8838, "lon": -43.1037},
    {"codigo_ibge": "3549805", "municipio": "São José do Rio Preto","uf": "SP", "lat": -20.8197, "lon": -49.3797},
    {"codigo_ibge": "3106705", "municipio": "Betim",                "uf": "MG", "lat": -19.9678, "lon": -44.1986},
    {"codigo_ibge": "3529401", "municipio": "Mauá",                 "uf": "SP", "lat": -23.6678, "lon": -46.4611},
    {"codigo_ibge": "3548500", "municipio": "Santos",               "uf": "SP", "lat": -23.9608, "lon": -46.3333},
    {"codigo_ibge": "3513801", "municipio": "Diadema",              "uf": "SP", "lat": -23.6867, "lon": -46.6228},
    {"codigo_ibge": "3143302", "municipio": "Montes Claros",        "uf": "MG", "lat": -16.7281, "lon": -43.8611},
    {"codigo_ibge": "3551702", "municipio": "São Vicente",          "uf": "SP", "lat": -23.9608, "lon": -46.3978},
    {"codigo_ibge": "3510609", "municipio": "Carapicuíba",          "uf": "SP", "lat": -23.5228, "lon": -46.8358},
    {"codigo_ibge": "3300456", "municipio": "Belford Roxo",         "uf": "RJ", "lat": -22.7644, "lon": -43.3994},
    {"codigo_ibge": "3538709", "municipio": "Piracicaba",           "uf": "SP", "lat": -22.7253, "lon": -47.6492},
    {"codigo_ibge": "3302403", "municipio": "Macaé",                "uf": "RJ", "lat": -22.3708, "lon": -41.7869},
    {"codigo_ibge": "3301009", "municipio": "Campos dos Goytacazes","uf": "RJ", "lat": -21.7545, "lon": -41.3244},
    # Sul (20)
    {"codigo_ibge": "4314902", "municipio": "Porto Alegre",         "uf": "RS", "lat": -30.0346, "lon": -51.2177},
    {"codigo_ibge": "4106902", "municipio": "Curitiba",             "uf": "PR", "lat": -25.4284, "lon": -49.2733},
    {"codigo_ibge": "4205407", "municipio": "Florianópolis",        "uf": "SC", "lat": -27.5954, "lon": -48.5480},
    {"codigo_ibge": "4113700", "municipio": "Londrina",             "uf": "PR", "lat": -23.3114, "lon": -51.1628},
    {"codigo_ibge": "4209102", "municipio": "Joinville",            "uf": "SC", "lat": -26.3045, "lon": -48.8487},
    {"codigo_ibge": "4305108", "municipio": "Caxias do Sul",        "uf": "RS", "lat": -29.1678, "lon": -51.1794},
    {"codigo_ibge": "4115200", "municipio": "Maringá",              "uf": "PR", "lat": -23.4251, "lon": -51.9386},
    {"codigo_ibge": "4304606", "municipio": "Canoas",               "uf": "RS", "lat": -29.9178, "lon": -51.1839},
    {"codigo_ibge": "4202404", "municipio": "Blumenau",             "uf": "SC", "lat": -26.9194, "lon": -49.0661},
    {"codigo_ibge": "4125506", "municipio": "São José dos Pinhais", "uf": "PR", "lat": -25.5369, "lon": -49.2072},
    {"codigo_ibge": "4204202", "municipio": "Chapecó",              "uf": "SC", "lat": -27.1005, "lon": -52.6150},
    {"codigo_ibge": "4108304", "municipio": "Foz do Iguaçu",        "uf": "PR", "lat": -25.5478, "lon": -54.5882},
    {"codigo_ibge": "4318705", "municipio": "São Leopoldo",         "uf": "RS", "lat": -29.7597, "lon": -51.1492},
    {"codigo_ibge": "4104808", "municipio": "Cascavel",             "uf": "PR", "lat": -24.9553, "lon": -53.4553},
    {"codigo_ibge": "4119905", "municipio": "Ponta Grossa",         "uf": "PR", "lat": -25.0944, "lon": -50.1611},
    {"codigo_ibge": "4314407", "municipio": "Pelotas",              "uf": "RS", "lat": -31.7654, "lon": -52.3376},
    {"codigo_ibge": "4313409", "municipio": "Novo Hamburgo",        "uf": "RS", "lat": -29.6803, "lon": -51.1303},
    {"codigo_ibge": "4216602", "municipio": "São José",             "uf": "SC", "lat": -27.5945, "lon": -48.6378},
    {"codigo_ibge": "4208203", "municipio": "Itajaí",               "uf": "SC", "lat": -26.9078, "lon": -48.6619},
    {"codigo_ibge": "4309209", "municipio": "Gravataí",             "uf": "RS", "lat": -29.9441, "lon": -50.9836},
]


def download_clima(ano_inicio: int = 2020, ano_fim: int = 2024) -> str:
    log(f"Clima: Open-Meteo Archive API — {len(CIDADES_CLIMA)} cidades ({ano_inicio}–{ano_fim})...")
    os.makedirs(DIRS["clima"], exist_ok=True)

    di, df  = f"{ano_inicio}-01-01", f"{ano_fim}-12-31"
    all_rows = []
    erros    = 0

    for i, cidade in enumerate(CIDADES_CLIMA, 1):
        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={cidade['lat']}&longitude={cidade['lon']}"
            f"&start_date={di}&end_date={df}"
            "&daily=temperature_2m_mean,precipitation_sum,wind_speed_10m_max"
            "&timezone=America%2FSao_Paulo"
        )
        try:
            data  = fetch(url, timeout=60)
            daily = data.get("daily", {})
            datas   = daily.get("time", [])
            temps   = daily.get("temperature_2m_mean", [])
            precips = daily.get("precipitation_sum", [])
            ventos  = daily.get("wind_speed_10m_max", [])
            for j, dt in enumerate(datas):
                all_rows.append({
                    "data":              dt,
                    "codigo_ibge":       cidade["codigo_ibge"],
                    "municipio":         cidade["municipio"],
                    "uf":                cidade["uf"],
                    "temperatura_media": temps[j]   if j < len(temps)   else None,
                    "precipitacao_mm":   precips[j]  if j < len(precips)  else None,
                    "vento_max_kmh":     ventos[j]   if j < len(ventos)   else None,
                })
        except Exception as e:
            log(f"  AVISO: {cidade['municipio']} ({cidade['uf']}) — {e}")
            erros += 1

        if i % 20 == 0:
            log(f"  {i}/{len(CIDADES_CLIMA)} cidades | {len(all_rows):,} registros até agora")
        time.sleep(0.25)  # respeitar rate limit Open-Meteo

    fields = ["data", "codigo_ibge", "municipio", "uf",
              "temperatura_media", "precipitacao_mm", "vento_max_kmh"]
    path = out("clima_historico.csv", "clima")
    write_csv(path, fields, all_rows)
    log(f"Clima: {len(all_rows):,} registros | {len(CIDADES_CLIMA) - erros} cidades OK | {erros} erros ->{path}")
    return path


# ─── entry point ──────────────────────────────────────────────────────────────

DATASETS = {
    # Macroeconomia — BCB
    "ptax":         download_ptax,
    "selic":        download_selic,
    "ipca":         download_ipca,
    "cdi":          download_cdi,
    "igpm":         download_igpm,
    "desemprego":   download_desemprego,
    "euro":         download_euro,
    # Calendário
    "feriados":     download_feriados,
    # Geografia — IBGE
    "municipios":   download_municipios,
    "populacao":    download_populacao,
    "pib":          download_pib,
    "renda":        download_renda,
    "escolaridade": download_escolaridade,
    # Clima — Open-Meteo
    "clima":        download_clima,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="BanVic - Download de dados externos")
    parser.add_argument("--dataset", choices=list(DATASETS) + ["all"], default="all",
                        help="Dataset a baixar (padrão: all)")
    parser.add_argument("--ano-inicio", type=int, default=2020,
                        help="Ano inicial para séries temporais (padrão: 2020)")
    parser.add_argument("--ano-fim",    type=int, default=2024,
                        help="Ano final para séries temporais (padrão: 2024)")
    parser.add_argument("--ignorar-erros", action="store_true",
                        help="Continuar mesmo se um dataset falhar")
    args = parser.parse_args()

    # Datasets que usam intervalo de anos via CLI
    COM_ANOS      = {"ptax", "selic", "cdi", "euro", "feriados", "clima"}
    # Datasets com intervalo fixo (histórico completo necessário)
    ANO_INICIO_FIXO = {"ipca": 2010, "igpm": 2010, "desemprego": 2015}

    targets = list(DATASETS.keys()) if args.dataset == "all" else [args.dataset]

    start = datetime.now()
    falhas = []
    for name in targets:
        fn = DATASETS[name]
        try:
            if name in COM_ANOS:
                fn(args.ano_inicio, args.ano_fim)
            elif name in ANO_INICIO_FIXO:
                fn(ANO_INICIO_FIXO[name], args.ano_fim)
            else:
                fn()
        except Exception as e:
            log(f"ERRO em {name}: {e}")
            falhas.append(name)
            if not args.ignorar_erros:
                sys.exit(1)

    elapsed = (datetime.now() - start).seconds
    status  = f"{len(falhas)} erro(s): {falhas}" if falhas else "todos OK"
    log(f"Concluído em {elapsed}s — {status}. Arquivos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
