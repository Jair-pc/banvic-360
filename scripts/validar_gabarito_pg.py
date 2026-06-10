"""
BanVic 360 -- Validador PostgreSQL vs Gabarito
================================================
Consulta as 8 KPI views Gold no PostgreSQL e compara com gabarito.json.
Esta e a prova real de que os projetos chegam nos valores corretos.

Uso:
    python scripts/validar_gabarito_pg.py
    python scripts/validar_gabarito_pg.py --tolerancia 0.01
    python scripts/validar_gabarito_pg.py --kpi 1
    python scripts/validar_gabarito_pg.py --gabarito docs/gabarito/gabarito.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent

PG_CONN = {
    "host":     os.getenv("PG_HOST", "localhost"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB", "banvic"),
    "user":     os.getenv("PG_USER", "banvic_user"),
    "password": os.getenv("PG_PASSWORD", "banvic_pass"),
}

TOLERANCIA_PADRAO = 0.01  # 1 centavo


# ─── Consultas Gold ──────────────────────────────────────────────────────────

def consultar_kpi1(cur) -> list[dict]:
    cur.execute("""
        SELECT cod_agencia, nome_agencia, qtd_contas,
               saldo_total, saldo_medio
        FROM gold.vw_kpi1_saldo_por_agencia
        ORDER BY saldo_total DESC
    """)
    return [dict(r) for r in cur.fetchall()]


def consultar_kpi2_3(cur) -> list[dict]:
    cur.execute("""
        SELECT ano, mes, nome_transacao,
               qtd_transacoes, volume_total, pct_mix
        FROM gold.vw_kpi2_3_transacoes_por_mes
        ORDER BY ano, mes, volume_total DESC
    """)
    return [dict(r) for r in cur.fetchall()]


def consultar_kpi4(cur) -> list[dict]:
    cur.execute("""
        SELECT status_proposta, qtd_propostas,
               valor_total_proposto, pct_status
        FROM gold.vw_kpi4_conversao_propostas
        ORDER BY status_proposta
    """)
    return [dict(r) for r in cur.fetchall()]


def consultar_kpi5(cur) -> list[dict]:
    cur.execute("""
        SELECT ranking, cod_agencia, nome_agencia,
               saldo_total, volume_total
        FROM gold.vw_kpi5_ranking_agencias
        ORDER BY ranking
    """)
    return [dict(r) for r in cur.fetchall()]


def consultar_kpi6(cur) -> list[dict]:
    cur.execute("""
        SELECT cod_colaborador, qtd_contas_geridas,
               saldo_gerido, propostas_aprovadas
        FROM gold.vw_kpi6_carteira_colaborador
        ORDER BY saldo_gerido DESC NULLS LAST
    """)
    return [dict(r) for r in cur.fetchall()]


def consultar_kpi7(cur) -> list[dict]:
    cur.execute("""
        SELECT faixa_etaria, qtd_clientes,
               ROUND(saldo_medio::numeric, 2) AS saldo_medio,
               ROUND(saldo_total::numeric, 2) AS saldo_total
        FROM gold.vw_kpi7_segmentacao_clientes
        ORDER BY faixa_etaria
    """)
    return [dict(r) for r in cur.fetchall()]


def consultar_kpi8(cur) -> list[dict]:
    cur.execute("""
        SELECT ano, mes,
               ROUND(indice_mes::numeric, 4)          AS indice_mes,
               ROUND(indice_base::numeric, 4)         AS indice_base,
               ROUND(volume_nominal::numeric, 2)      AS volume_nominal,
               ROUND(volume_real_moeda_atual::numeric, 2) AS volume_real
        FROM gold.vw_kpi8_correcao_ipca
        ORDER BY ano, mes
    """)
    return [dict(r) for r in cur.fetchall()]


CONSULTAS = {
    1:     consultar_kpi1,
    "2_3": consultar_kpi2_3,
    4:     consultar_kpi4,
    5:     consultar_kpi5,
    6:     consultar_kpi6,
    7:     consultar_kpi7,
    8:     consultar_kpi8,
}


# ─── Comparacao ──────────────────────────────────────────────────────────────

def comparar_totais(kpi_id, dados_pg: list[dict], dados_gabarito: list[dict],
                    tolerancia: float) -> dict:
    """
    Compara os totais numericos agregados de cada KPI.
    Nao compara linha a linha (IDs e ordenacoes podem diferir).
    """
    resultado = {"kpi": kpi_id, "status": "OK", "detalhes": []}

    def soma(dados, campo):
        return sum(float(r.get(campo, 0) or 0) for r in dados if r.get(campo) is not None)

    if kpi_id == 1:
        total_pg  = soma(dados_pg, "saldo_total")
        total_gab = soma(dados_gabarito, "saldo_total")
        diff = abs(total_pg - total_gab)
        ok = diff <= tolerancia
        resultado["detalhes"].append({
            "campo": "saldo_total (soma)",
            "pg": round(total_pg, 2),
            "gabarito": round(total_gab, 2),
            "diferenca": round(diff, 2),
            "ok": ok,
        })
        if not ok:
            resultado["status"] = "FALHA"

    elif kpi_id == "2_3":
        total_pg  = soma(dados_pg, "volume_total")
        total_gab = soma(dados_gabarito, "volume")
        diff = abs(total_pg - total_gab)
        ok = diff <= tolerancia
        resultado["detalhes"].append({
            "campo": "volume_total (soma geral)",
            "pg": round(total_pg, 2),
            "gabarito": round(total_gab, 2),
            "diferenca": round(diff, 2),
            "ok": ok,
        })
        if not ok:
            resultado["status"] = "FALHA"

    elif kpi_id == 4:
        for row_gab in dados_gabarito:
            status = row_gab["status_proposta"]
            row_pg = next((r for r in dados_pg if r["status_proposta"] == status), None)
            if row_pg is None:
                resultado["detalhes"].append({"campo": f"status={status}", "ok": False, "erro": "ausente no PG"})
                resultado["status"] = "FALHA"
                continue
            diff = abs(float(row_pg["qtd_propostas"]) - float(row_gab["qtd_propostas"]))
            ok = diff == 0
            resultado["detalhes"].append({
                "campo": f"qtd_propostas status={status}",
                "pg": row_pg["qtd_propostas"],
                "gabarito": row_gab["qtd_propostas"],
                "diferenca": diff,
                "ok": ok,
            })
            if not ok:
                resultado["status"] = "FALHA"

    elif kpi_id == 5:
        qtd_pg  = len(dados_pg)
        qtd_gab = len(dados_gabarito)
        ok = qtd_pg == qtd_gab
        resultado["detalhes"].append({
            "campo": "qtd_agencias no ranking",
            "pg": qtd_pg,
            "gabarito": qtd_gab,
            "ok": ok,
        })
        top1_pg  = str(dados_pg[0]["cod_agencia"]) if dados_pg else None
        top1_gab = str(dados_gabarito[0]["cod_agencia"]) if dados_gabarito else None
        ok2 = top1_pg == top1_gab
        resultado["detalhes"].append({
            "campo": "1a agencia no ranking",
            "pg": top1_pg,
            "gabarito": top1_gab,
            "ok": ok2,
        })
        if not ok or not ok2:
            resultado["status"] = "FALHA"

    elif kpi_id == 6:
        total_pg  = soma(dados_pg,  "saldo_gerido")
        total_gab = soma(dados_gabarito, "saldo_gerido")
        diff = abs(total_pg - total_gab)
        tolerancia_rel = total_gab * 0.01  # 1% de tolerancia para top-20
        ok = diff <= max(tolerancia_rel, tolerancia)
        resultado["detalhes"].append({
            "campo": "saldo_gerido top-20 (soma)",
            "pg": round(total_pg, 2),
            "gabarito": round(total_gab, 2),
            "diferenca": round(diff, 2),
            "ok": ok,
        })
        if not ok:
            resultado["status"] = "FALHA"

    elif kpi_id == 7:
        for row_gab in dados_gabarito:
            fx = row_gab["faixa_etaria"]
            row_pg = next((r for r in dados_pg if r["faixa_etaria"] == fx), None)
            if row_pg is None:
                resultado["detalhes"].append({"campo": f"faixa={fx}", "ok": False, "erro": "ausente no PG"})
                resultado["status"] = "FALHA"
                continue
            diff = abs(float(row_pg["qtd_clientes"]) - float(row_gab["qtd_clientes"]))
            ok = diff == 0
            resultado["detalhes"].append({
                "campo": f"qtd_clientes faixa={fx}",
                "pg": row_pg["qtd_clientes"],
                "gabarito": row_gab["qtd_clientes"],
                "diferenca": diff,
                "ok": ok,
            })
            if not ok:
                resultado["status"] = "FALHA"

    elif kpi_id == 8:
        total_pg  = soma(dados_pg, "volume_nominal")
        total_gab = soma(dados_gabarito, "volume_nominal")
        diff = abs(total_pg - total_gab)
        ok = diff <= tolerancia
        resultado["detalhes"].append({
            "campo": "volume_nominal (soma geral)",
            "pg": round(total_pg, 2),
            "gabarito": round(total_gab, 2),
            "diferenca": round(diff, 2),
            "ok": ok,
        })
        if not ok:
            resultado["status"] = "FALHA"

    return resultado


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BanVic 360 -- Validador PG vs Gabarito")
    parser.add_argument("--gabarito", default=str(ROOT / "docs" / "gabarito" / "gabarito.json"))
    parser.add_argument("--tolerancia", type=float, default=TOLERANCIA_PADRAO)
    parser.add_argument("--kpi", type=str, default="todos")
    args = parser.parse_args()

    gabarito_path = Path(args.gabarito)
    if not gabarito_path.exists():
        print(f"ERRO: gabarito nao encontrado em {gabarito_path}")
        print("Execute primeiro: python scripts/validar_gabarito.py")
        sys.exit(1)

    with open(gabarito_path, encoding="utf-8") as f:
        gabarito = json.load(f)

    try:
        conn = psycopg2.connect(**PG_CONN, cursor_factory=psycopg2.extras.RealDictCursor)
    except psycopg2.OperationalError as e:
        print(f"ERRO ao conectar no PostgreSQL: {e}")
        sys.exit(1)

    resultados = []
    falhas = 0

    with conn:
        cur = conn.cursor()
        for kpi_gab in gabarito:
            kpi_id = kpi_gab["kpi"]
            if args.kpi != "todos" and str(kpi_id) != args.kpi:
                continue

            consulta_fn = CONSULTAS.get(kpi_id)
            if not consulta_fn:
                print(f"  KPI {kpi_id}: sem consulta mapeada, pulando.")
                continue

            try:
                dados_pg = consulta_fn(cur)
            except Exception as e:
                print(f"  KPI {kpi_id}: ERRO na consulta: {e}")
                resultados.append({"kpi": kpi_id, "status": "ERRO", "detalhes": [str(e)]})
                falhas += 1
                continue

            resultado = comparar_totais(kpi_id, dados_pg, kpi_gab.get("dados", []), args.tolerancia)
            resultados.append(resultado)

            icone = "OK" if resultado["status"] == "OK" else "FALHA"
            print(f"  KPI {kpi_id}: {icone}")
            for det in resultado["detalhes"]:
                status_det = "  OK" if det.get("ok") else "  FALHA"
                campo = det.get("campo", "")
                if "erro" in det:
                    print(f"    {status_det} {campo}: {det['erro']}")
                else:
                    print(f"    {status_det} {campo}: PG={det.get('pg')}  GAB={det.get('gabarito')}  diff={det.get('diferenca')}")

            if resultado["status"] != "OK":
                falhas += 1

    conn.close()

    print("")
    print("=" * 50)
    total = len(resultados)
    ok    = total - falhas
    print(f"Resultado: {ok}/{total} KPIs corretos")
    if falhas == 0:
        print("APROVADO: todos os KPIs batem com o gabarito.")
    else:
        print(f"REPROVADO: {falhas} KPI(s) com divergencia.")
    print("=" * 50)

    sys.exit(0 if falhas == 0 else 1)


if __name__ == "__main__":
    main()
