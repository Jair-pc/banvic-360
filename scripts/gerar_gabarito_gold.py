"""
BanVic 360 -- Gerador de Gabarito a partir do Gold PostgreSQL
=============================================================
Substitui o gabarito.json baseado em CSV pelo gabarito derivado
do Gold layer (Projeto 1 SQL Puro), que inclui dados sinteticos.

Todos os 9 projetos devem reproduzir exatamente estes numeros.

Uso:
    python scripts/gerar_gabarito_gold.py
    python scripts/gerar_gabarito_gold.py --output docs/gabarito/
"""

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


def _fetch(cur, sql) -> list[dict]:
    cur.execute(sql)
    return [dict(r) for r in cur.fetchall()]


def gerar_kpi1(cur) -> dict:
    dados = _fetch(cur, """
        SELECT cod_agencia, nome_agencia, qtd_contas,
               ROUND(saldo_total::numeric, 2) AS saldo_total,
               ROUND(saldo_medio::numeric, 2) AS saldo_medio
        FROM gold.vw_kpi1_saldo_por_agencia
        ORDER BY saldo_total DESC
    """)
    # ranking manual
    for i, r in enumerate(dados, 1):
        r["ranking"] = i
        r["cod_agencia"] = str(r["cod_agencia"])
    return {"kpi": 1, "nome": "Saldo sob gestao por agencia", "dados": dados}


def gerar_kpi2_3(cur) -> dict:
    dados = _fetch(cur, """
        SELECT ano, mes, mes_nome,
               nome_transacao,
               qtd_transacoes,
               ROUND(volume_total::numeric, 2) AS volume,
               pct_mix
        FROM gold.vw_kpi2_3_transacoes_por_mes
        ORDER BY ano, mes, volume DESC
    """)
    for r in dados:
        r["ano_mes"] = f"{r['ano']}-{int(r['mes']):02d}"
    return {"kpi": "2_3", "nome": "Volume e mix de transacoes por mes", "dados": dados}


def gerar_kpi4(cur) -> dict:
    dados = _fetch(cur, """
        SELECT status_proposta,
               qtd_propostas,
               ROUND(valor_total_proposto::numeric, 2) AS valor_total_proposto,
               ROUND((valor_total_proposto / qtd_propostas)::numeric, 2) AS valor_medio,
               pct_status
        FROM gold.vw_kpi4_conversao_propostas
        ORDER BY qtd_propostas DESC
    """)
    return {"kpi": 4, "nome": "Conversao de propostas", "dados": dados}


def gerar_kpi5(cur) -> dict:
    dados = _fetch(cur, """
        SELECT ranking, cod_agencia, nome_agencia, cidade, uf,
               qtd_contas,
               ROUND(saldo_total::numeric, 2) AS saldo_total,
               ROUND(saldo_medio::numeric, 2) AS saldo_medio,
               ROUND(volume_total::numeric, 2) AS volume_total
        FROM gold.vw_kpi5_ranking_agencias
        ORDER BY ranking
    """)
    for r in dados:
        r["cod_agencia"] = str(r["cod_agencia"])
    return {"kpi": 5, "nome": "Ranking de agencias", "dados": dados}


def gerar_kpi6(cur) -> dict:
    dados = _fetch(cur, """
        SELECT cod_colaborador, nome_completo AS nome,
               qtd_contas_geridas,
               ROUND(saldo_gerido::numeric, 2) AS saldo_gerido,
               propostas_aprovadas
        FROM gold.vw_kpi6_carteira_colaborador
        ORDER BY saldo_gerido DESC NULLS LAST
    """)
    for r in dados:
        r["cod_colaborador"] = str(r["cod_colaborador"])
    return {"kpi": 6, "nome": "Carteira por colaborador", "dados": dados}


def gerar_kpi7(cur) -> dict:
    dados = _fetch(cur, """
        SELECT faixa_etaria,
               qtd_clientes,
               ROUND(saldo_medio::numeric, 2) AS saldo_medio,
               ROUND(saldo_total::numeric, 2) AS saldo_total
        FROM gold.vw_kpi7_segmentacao_clientes
        ORDER BY faixa_etaria
    """)
    return {"kpi": 7, "nome": "Segmentacao por faixa etaria", "dados": dados}


def gerar_kpi8(cur) -> dict:
    rows = _fetch(cur, """
        SELECT ano, mes, mes_nome,
               ROUND(indice_mes::numeric, 4) AS indice_mes,
               ROUND(indice_base::numeric, 4) AS indice_base,
               ROUND(volume_nominal::numeric, 2) AS volume_nominal,
               ROUND(volume_real_moeda_atual::numeric, 2) AS volume_real
        FROM gold.vw_kpi8_correcao_ipca
        ORDER BY ano, mes
    """)
    for r in rows:
        r["ano_mes"] = f"{r['ano']}-{int(r['mes']):02d}"

    indice_base = rows[-1]["indice_base"] if rows else None
    mes_base = rows[-1]["ano_mes"] if rows else None
    return {
        "kpi": 8,
        "nome": "Correcao IPCA",
        "mes_base": mes_base,
        "indice_base": float(indice_base) if indice_base else None,
        "dados": rows,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "docs" / "gabarito"))
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = psycopg2.connect(**PG_CONN, cursor_factory=psycopg2.extras.RealDictCursor)
    except psycopg2.OperationalError as e:
        print(f"ERRO ao conectar no PostgreSQL: {e}")
        sys.exit(1)

    print("Gerando gabarito a partir do Gold PostgreSQL...")

    geradores = [
        gerar_kpi1, gerar_kpi2_3, gerar_kpi4, gerar_kpi5,
        gerar_kpi6, gerar_kpi7, gerar_kpi8,
    ]

    gabarito = []
    with conn:
        cur = conn.cursor()
        for fn in geradores:
            try:
                resultado = fn(cur)
                n = len(resultado.get("dados", []))
                print(f"  KPI {resultado['kpi']}: {n} linhas")
                gabarito.append(resultado)
            except Exception as e:
                print(f"  KPI {fn.__name__}: ERRO: {e}")
                raise

    conn.close()

    # Serializar decimais
    def default_serial(obj):
        from decimal import Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Tipo nao serializavel: {type(obj)}")

    gabarito_path = out_dir / "gabarito.json"
    with open(gabarito_path, "w", encoding="utf-8") as f:
        json.dump(gabarito, f, ensure_ascii=False, indent=2, default=default_serial)

    print(f"\nGabarito salvo em: {gabarito_path}")
    print(f"Total de KPIs: {len(gabarito)}")

    # Resumo
    for k in gabarito:
        n = len(k.get("dados", []))
        print(f"  KPI {k['kpi']}: {n} registros")


if __name__ == "__main__":
    main()
