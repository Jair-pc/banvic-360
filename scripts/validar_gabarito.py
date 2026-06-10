"""
BanVic 360 -- Validador do Gabarito (Fase 0)
============================================
Calcula os 8 KPIs diretamente dos CSVs originais (sem PostgreSQL).
Gera gabarito.json e gabarito_resumo.txt para comparacao futura.

Os 9 projetos devem chegar exatamente nestes numeros.

Uso:
    python scripts/validar_gabarito.py
    python scripts/validar_gabarito.py --output docs/gabarito/
    python scripts/validar_gabarito.py --kpi 1         (so KPI especifico)
"""

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA         = PROJECT_ROOT / "data" / "banvic"
EXT          = PROJECT_ROOT / "external_data"
OUT_DEFAULT  = PROJECT_ROOT / "docs" / "gabarito"


# ─── Leitura dos CSVs originais ──────────────────────────────────────────────

def ler_csv(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ─── KPI 1: Saldo sob gestao por agencia ─────────────────────────────────────

def kpi1_saldo_por_agencia(contas, agencias) -> dict:
    """SUM(saldo_total) GROUP BY agencia -- snapshot atual (todas as contas)."""
    ag_map = {a["cod_agencia"]: a["nome"] for a in agencias}
    ag_cidade = {a["cod_agencia"]: a["cidade"] for a in agencias}
    ag_uf     = {a["cod_agencia"]: a["uf"] for a in agencias}

    saldos = defaultdict(float)
    qtd    = defaultdict(int)
    for c in contas:
        ag = c["cod_agencia"]
        try:
            saldos[ag] += float(c["saldo_total"])
            qtd[ag] += 1
        except (ValueError, KeyError):
            pass

    resultado = []
    for ag, saldo in sorted(saldos.items(), key=lambda x: -x[1]):
        resultado.append({
            "cod_agencia":  ag,
            "nome_agencia": ag_map.get(ag, ""),
            "cidade":       ag_cidade.get(ag, ""),
            "uf":           ag_uf.get(ag, ""),
            "qtd_contas":   qtd[ag],
            "saldo_total":  round(saldo, 2),
            "saldo_medio":  round(saldo / qtd[ag], 2) if qtd[ag] else 0,
        })
    return {"kpi": 1, "nome": "Saldo sob gestao por agencia", "dados": resultado}


# ─── KPI 2 e 3: Volume e mix de transacoes por mes ───────────────────────────

def kpi2_3_transacoes_por_mes(transacoes) -> dict:
    """SUM(valor), COUNT GROUP BY ano, mes, nome_transacao + % mix."""
    agrup = defaultdict(lambda: {"qtd": 0, "volume": 0.0})

    for tx in transacoes:
        try:
            dt    = tx["data_transacao"][:7]  # YYYY-MM
            nome  = tx["nome_transacao"]
            valor = abs(float(tx["valor_transacao"]))
            agrup[(dt, nome)]["qtd"]    += 1
            agrup[(dt, nome)]["volume"] += valor
        except (ValueError, KeyError):
            pass

    # Total por mes para calcular mix
    total_mes = defaultdict(float)
    for (dt, nome), v in agrup.items():
        total_mes[dt] += v["volume"]

    resultado = []
    for (dt, nome), v in sorted(agrup.items()):
        resultado.append({
            "ano_mes":      dt,
            "nome_transacao": nome,
            "qtd":          v["qtd"],
            "volume":       round(v["volume"], 2),
            "pct_mix":      round(v["volume"] / total_mes[dt] * 100, 2) if total_mes[dt] else 0,
        })

    return {"kpi": "2_3", "nome": "Volume e mix de transacoes por mes", "dados": resultado}


# ─── KPI 4: Conversao de propostas ───────────────────────────────────────────

def kpi4_conversao_propostas(propostas) -> dict:
    """COUNT por status_proposta + valor medio."""
    agrup = defaultdict(lambda: {"qtd": 0, "valor_total": 0.0})
    for p in propostas:
        status = p.get("status_proposta", "")
        try:
            valor = float(p.get("valor_proposta", 0))
        except ValueError:
            valor = 0.0
        agrup[status]["qtd"] += 1
        agrup[status]["valor_total"] += valor

    total = sum(v["qtd"] for v in agrup.values())
    resultado = []
    for status, v in sorted(agrup.items()):
        resultado.append({
            "status_proposta":  status,
            "qtd_propostas":    v["qtd"],
            "valor_total":      round(v["valor_total"], 2),
            "valor_medio":      round(v["valor_total"] / v["qtd"], 2) if v["qtd"] else 0,
            "pct_status":       round(v["qtd"] / total * 100, 2) if total else 0,
        })

    return {"kpi": 4, "nome": "Conversao de propostas", "dados": resultado}


# ─── KPI 5: Ranking de agencias ──────────────────────────────────────────────

def kpi5_ranking_agencias(resultado_kpi1) -> dict:
    """Mesmo que KPI 1, mas com ranking explicito."""
    dados = resultado_kpi1["dados"]
    for i, row in enumerate(dados, 1):
        row["ranking"] = i

    return {"kpi": 5, "nome": "Ranking de agencias", "dados": dados}


# ─── KPI 6: Carteira por colaborador ─────────────────────────────────────────

def kpi6_carteira_colaborador(contas, propostas, colaboradores) -> dict:
    """contas geridas, saldo total, propostas aprovadas por colaborador."""
    col_map = {}
    for c in colaboradores:
        cod = c["cod_colaborador"]
        col_map[cod] = {
            "primeiro_nome": c.get("primeiro_nome", ""),
            "ultimo_nome":   c.get("ultimo_nome", ""),
        }

    agrup = defaultdict(lambda: {"qtd_contas": 0, "saldo_total": 0.0})
    for c in contas:
        cod = c.get("cod_colaborador", "")
        try:
            agrup[cod]["qtd_contas"] += 1
            agrup[cod]["saldo_total"] += float(c["saldo_total"])
        except (ValueError, KeyError):
            pass

    props_aprov = defaultdict(int)
    for p in propostas:
        if p.get("status_proposta", "").lower() in ("aprovada", "aprovado"):
            props_aprov[p.get("cod_colaborador", "")] += 1

    resultado = []
    for cod, v in sorted(agrup.items(), key=lambda x: -x[1]["saldo_total"]):
        info = col_map.get(cod, {})
        resultado.append({
            "cod_colaborador":      cod,
            "nome":                 f"{info.get('primeiro_nome','')} {info.get('ultimo_nome','')}".strip(),
            "qtd_contas_geridas":   v["qtd_contas"],
            "saldo_gerido":         round(v["saldo_total"], 2),
            "propostas_aprovadas":  props_aprov.get(cod, 0),
        })

    return {"kpi": 6, "nome": "Carteira por colaborador", "dados": resultado}


# ─── KPI 7: Segmentacao por faixa etaria ─────────────────────────────────────

def kpi7_segmentacao_etaria(clientes, contas) -> dict:
    """Faixas etarias vs saldo medio."""
    def faixa(dt_nasc: str) -> str:
        try:
            nasc = date.fromisoformat(dt_nasc[:10])
            idade = (date.today() - nasc).days // 365
        except (ValueError, TypeError):
            return "Desconhecido"
        for upper, label in [(24,"18-24"),(34,"25-34"),(44,"35-44"),(54,"45-54"),(64,"55-64")]:
            if idade <= upper:
                return label
        return "65+"

    cli_faixa = {}
    for c in clientes:
        cli_faixa[c["cod_cliente"]] = faixa(c.get("data_nascimento",""))

    # Conta -> faixa via cliente
    conta_cli = {c["num_conta"]: c["cod_cliente"] for c in contas}

    agrup = defaultdict(lambda: {"qtd_clientes": set(), "saldos": []})
    for c in contas:
        cod_cli = c.get("cod_cliente", "")
        fx = cli_faixa.get(cod_cli, "Desconhecido")
        try:
            agrup[fx]["qtd_clientes"].add(cod_cli)
            agrup[fx]["saldos"].append(float(c["saldo_total"]))
        except (ValueError, KeyError):
            pass

    resultado = []
    for fx in ["18-24","25-34","35-44","45-54","55-64","65+","Desconhecido"]:
        if fx not in agrup:
            continue
        v = agrup[fx]
        saldos = v["saldos"]
        resultado.append({
            "faixa_etaria":  fx,
            "qtd_clientes":  len(v["qtd_clientes"]),
            "qtd_contas":    len(saldos),
            "saldo_medio":   round(sum(saldos) / len(saldos), 2) if saldos else 0,
            "saldo_total":   round(sum(saldos), 2),
        })

    return {"kpi": 7, "nome": "Segmentacao por faixa etaria", "dados": resultado}


# ─── KPI 8: Correcao IPCA ────────────────────────────────────────────────────

def kpi8_correcao_ipca(transacoes, ipca_dados) -> dict:
    """valor_real = valor_nominal x indice_base / indice_mes."""
    # Construir mapa ano-mes -> indice
    ipca_map = {}
    for r in ipca_dados:
        chave = f"{r['ano']}-{int(r['mes_num']):02d}"
        try:
            ipca_map[chave] = float(r["indice"])
        except (ValueError, KeyError):
            pass

    if not ipca_map:
        return {"kpi": 8, "nome": "Correcao IPCA", "erro": "IPCA nao carregado"}

    # Indice base = ultimo mes disponivel
    chave_base = max(ipca_map.keys())
    indice_base = ipca_map[chave_base]

    # Agrupar volume nominal por mes
    vol_mes = defaultdict(float)
    for tx in transacoes:
        try:
            dt    = tx["data_transacao"][:7]
            valor = abs(float(tx["valor_transacao"]))
            vol_mes[dt] += valor
        except (ValueError, KeyError):
            pass

    resultado = []
    for dt in sorted(vol_mes.keys()):
        indice_mes = ipca_map.get(dt)
        if not indice_mes:
            continue
        vol_nominal = vol_mes[dt]
        vol_real    = vol_nominal * indice_base / indice_mes
        resultado.append({
            "ano_mes":          dt,
            "indice_mes":       indice_mes,
            "indice_base":      indice_base,
            "mes_base":         chave_base,
            "volume_nominal":   round(vol_nominal, 2),
            "volume_real":      round(vol_real, 2),
            "fator_correcao":   round(indice_base / indice_mes, 6),
        })

    return {
        "kpi": 8,
        "nome": "Correcao IPCA",
        "mes_base": chave_base,
        "indice_base": indice_base,
        "dados": resultado,
    }


# ─── Totais e resumo ─────────────────────────────────────────────────────────

def resumo_numerico(kpis: list[dict]) -> str:
    linhas = ["=" * 60, "GABARITO BANVIC 360 -- RESUMO NUMERICO", "=" * 60]

    for k in kpis:
        linhas.append(f"\nKPI {k['kpi']}: {k['nome']}")
        linhas.append("-" * 50)

        if k.get("erro"):
            linhas.append(f"  ERRO: {k['erro']}")
            continue

        dados = k.get("dados", [])
        if not dados:
            linhas.append("  (sem dados)")
            continue

        if k["kpi"] == 1:
            total = sum(d["saldo_total"] for d in dados)
            linhas.append(f"  Total geral: R$ {total:,.2f}")
            for d in dados[:5]:
                linhas.append(f"  {d['nome_agencia']:<35} R$ {d['saldo_total']:>15,.2f}  ({d['qtd_contas']} contas)")
            if len(dados) > 5:
                linhas.append(f"  ... (+{len(dados)-5} agencias)")

        elif k["kpi"] == "2_3":
            meses = sorted(set(d["ano_mes"] for d in dados))
            linhas.append(f"  Periodo: {meses[0]} a {meses[-1]} ({len(meses)} meses)")
            total_vol = sum(d["volume"] for d in dados)
            total_qtd = sum(d["qtd"] for d in dados)
            linhas.append(f"  Total transacoes: {total_qtd:,}")
            linhas.append(f"  Volume total: R$ {total_vol:,.2f}")

        elif k["kpi"] == 4:
            for d in dados:
                linhas.append(f"  {d['status_proposta']:<20} {d['qtd_propostas']:>5} propostas  "
                               f"R$ {d['valor_medio']:>12,.2f} medio  ({d['pct_status']:.1f}%)")

        elif k["kpi"] == 5:
            for d in dados[:5]:
                linhas.append(f"  #{d['ranking']:>2} {d['nome_agencia']:<35} R$ {d['saldo_total']:>15,.2f}")

        elif k["kpi"] == 6:
            top = sorted(dados, key=lambda x: -x["saldo_gerido"])[:5]
            for d in top:
                linhas.append(f"  {d['nome']:<35} {d['qtd_contas_geridas']:>4} contas  "
                               f"R$ {d['saldo_gerido']:>15,.2f}")

        elif k["kpi"] == 7:
            for d in dados:
                linhas.append(f"  {d['faixa_etaria']:<10} {d['qtd_clientes']:>5} clientes  "
                               f"saldo medio R$ {d['saldo_medio']:>12,.2f}")

        elif k["kpi"] == 8:
            linhas.append(f"  Mes base: {k.get('mes_base','')} (indice {k.get('indice_base','')})")
            if dados:
                linhas.append(f"  Periodo: {dados[0]['ano_mes']} a {dados[-1]['ano_mes']}")
                total_nom  = sum(d["volume_nominal"] for d in dados)
                total_real = sum(d["volume_real"] for d in dados)
                linhas.append(f"  Volume nominal total: R$ {total_nom:,.2f}")
                linhas.append(f"  Volume real total:    R$ {total_real:,.2f}")
                linhas.append(f"  Ganho pelo IPCA:      R$ {total_real - total_nom:,.2f}")

    linhas.append("\n" + "=" * 60)
    return "\n".join(linhas)


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BanVic -- Validador do Gabarito")
    parser.add_argument("--output", default=str(OUT_DEFAULT))
    parser.add_argument("--kpi", type=str, default="todos",
                        help="Numero do KPI (1-8) ou 'todos'")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Carregando dados originais...")
    clientes     = ler_csv(DATA / "clientes.csv")
    contas       = ler_csv(DATA / "contas.csv")
    agencias     = ler_csv(DATA / "agencias.csv")
    colaboradores= ler_csv(DATA / "colaboradores.csv")
    transacoes   = ler_csv(DATA / "transacoes.csv")
    propostas    = ler_csv(DATA / "propostas_credito.csv")

    ipca_path = EXT / "macroeconomia" / "ipca.csv"
    ipca_dados = ler_csv(ipca_path) if ipca_path.exists() else []

    print(f"  clientes: {len(clientes):,}")
    print(f"  contas: {len(contas):,}")
    print(f"  transacoes: {len(transacoes):,}")
    print(f"  propostas: {len(propostas):,}")
    print(f"  ipca: {len(ipca_dados):,} meses")

    print("\nCalculando KPIs...")
    kpi1 = kpi1_saldo_por_agencia(contas, agencias)
    kpis = [
        kpi1,
        kpi2_3_transacoes_por_mes(transacoes),
        kpi4_conversao_propostas(propostas),
        kpi5_ranking_agencias(kpi1),
        kpi6_carteira_colaborador(contas, propostas, colaboradores),
        kpi7_segmentacao_etaria(clientes, contas),
        kpi8_correcao_ipca(transacoes, ipca_dados),
    ]

    # Filtrar por KPI especifico se solicitado
    if args.kpi != "todos":
        kpis = [k for k in kpis if str(k["kpi"]) == args.kpi]

    # Salvar JSON
    gabarito_file = out_dir / "gabarito.json"
    with open(gabarito_file, "w", encoding="utf-8") as f:
        json.dump(kpis, f, ensure_ascii=False, indent=2)
    print(f"\nGabarito salvo: {gabarito_file}")

    # Salvar resumo texto
    resumo = resumo_numerico(kpis)
    resumo_file = out_dir / "gabarito_resumo.txt"
    with open(resumo_file, "w", encoding="utf-8") as f:
        f.write(resumo)
    print(f"Resumo salvo:   {resumo_file}")

    # Imprimir resumo no console (ASCII-safe)
    print("\n" + resumo)


if __name__ == "__main__":
    main()
