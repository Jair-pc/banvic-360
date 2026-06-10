"""
BanVic 360 -- Carga Bronze (client-side)
=========================================
Usa psycopg2.copy_expert para carregar todos os CSVs no schema bronze.
Funciona com PostgreSQL em Docker (ao contrario do COPY FROM server-side).

Uso:
    python scripts/carga_bronze.py
    python scripts/carga_bronze.py --grupo banvic
    python scripts/carga_bronze.py --grupo sintetico
    python scripts/carga_bronze.py --grupo externo
"""

import argparse
import csv
import io
import os
import sys
import time
from pathlib import Path

import psycopg2
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

# ─── Mapa de cargas: (grupo, tabela, colunas, arquivo_relativo) ───────────────

CARGAS = [
    # ── BANVIC ORIGINAL ──────────────────────────────────────────────────────
    ("banvic", "bronze.clientes",
     "cod_cliente,primeiro_nome,ultimo_nome,email,tipo_cliente,data_inclusao,cpfcnpj,data_nascimento,endereco,cep",
     "data/banvic/clientes.csv"),

    ("banvic", "bronze.contas",
     "num_conta,cod_cliente,cod_agencia,cod_colaborador,tipo_conta,data_abertura,saldo_total,saldo_disponivel,data_ultimo_lancamento",
     "data/banvic/contas.csv"),

    ("banvic", "bronze.agencias",
     "cod_agencia,nome,endereco,cidade,uf,data_abertura,tipo_agencia",
     "data/banvic/agencias.csv"),

    ("banvic", "bronze.colaboradores",
     "cod_colaborador,primeiro_nome,ultimo_nome,email,cpf,data_nascimento,endereco,cep",
     "data/banvic/colaboradores.csv"),

    ("banvic", "bronze.colaborador_agencia",
     "cod_colaborador,cod_agencia",
     "data/banvic/colaborador_agencia.csv"),

    ("banvic", "bronze.propostas_credito",
     "cod_proposta,cod_cliente,cod_colaborador,data_entrada_proposta,taxa_juros_mensal,valor_proposta,valor_financiamento,valor_entrada,valor_prestacao,quantidade_parcelas,carencia,status_proposta",
     "data/banvic/propostas_credito.csv"),

    ("banvic", "bronze.transacoes",
     "cod_transacao,num_conta,data_transacao,nome_transacao,valor_transacao",
     "data/banvic/transacoes.csv"),

    # ── DADOS SINTETICOS ──────────────────────────────────────────────────────
    ("sintetico", "bronze.agencias_expandidas",
     "cod_agencia,nome,tipo_agencia,endereco,cidade,uf,cep,regiao,data_abertura,data_encerramento,eh_ativa,meta_comercial_mensal,latitude,longitude",
     "data/sintetico/agencias_expandidas.csv"),

    ("sintetico", "bronze.colaboradores_expandidos",
     "cod_colaborador,primeiro_nome,ultimo_nome,email,cpf,data_nascimento,cidade,uf,regiao,cargo,nivel_hierarquico,departamento,salario_base,cod_agencia,data_admissao,data_demissao,eh_ativo",
     "data/sintetico/colaboradores_expandidos.csv"),

    ("sintetico", "bronze.clientes_sinteticos",
     "cod_cliente,primeiro_nome,ultimo_nome,email,tipo_cliente,data_inclusao,cpfcnpj,data_nascimento,cidade,uf,cep,renda_mensal,faixa_renda,profissao,escolaridade,score_credito,faixa_score,idade,faixa_etaria",
     "data/sintetico/clientes_sinteticos.csv"),

    ("sintetico", "bronze.contas_sinteticas",
     "num_conta,cod_cliente,cod_agencia,cod_colaborador,tipo_conta,data_abertura,saldo_total,saldo_disponivel,data_ultimo_lancamento,flag_ativa",
     "data/sintetico/contas_sinteticas.csv"),

    ("sintetico", "bronze.transacoes_sinteticas",
     "cod_transacao,num_conta,data_transacao,nome_transacao,valor_transacao",
     "data/sintetico/transacoes_sinteticas.csv"),

    ("sintetico", "bronze.propostas_sinteticas",
     "cod_proposta,cod_cliente,cod_colaborador,data_entrada_proposta,taxa_juros_mensal,valor_proposta,valor_financiamento,valor_entrada,valor_prestacao,quantidade_parcelas,carencia,status_proposta,produto",
     "data/sintetico/propostas_sinteticas.csv"),

    ("sintetico", "bronze.investimentos",
     "id_investimento,cod_cliente,cod_agencia,cod_produto,nome_produto,indexador,data_aplicacao,data_vencimento,valor_aplicado,valor_atual,rentabilidade_pct,status,data_resgate,valor_resgate",
     "data/sintetico/investimentos.csv"),

    ("sintetico", "bronze.cartoes",
     "id_fatura,cod_cliente,cod_agencia,cod_produto,nome_produto,mes_referencia,limite_total,limite_disponivel,gasto_mes,valor_fatura,valor_pago,valor_parcelado,qtd_parcelas,dias_atraso,taxa_rotativo_mes,pct_utilizacao",
     "data/sintetico/cartoes.csv"),

    ("sintetico", "bronze.seguros",
     "id_apolice,num_apolice,cod_cliente,cod_agencia,cod_produto,nome_produto,data_inicio,data_fim,valor_segurado,premio_mensal,valor_sinistro,status_apolice,motivo_cancelamento,foi_cross_sell",
     "data/sintetico/seguros.csv"),

    ("sintetico", "bronze.inadimplencia",
     "id_inadimplencia,cod_contrato,tipo_contrato,cod_cliente,data_referencia,valor_total_contrato,valor_aberto,dias_atraso,bucket,score_credito,faixa_risco,valor_recuperado,flag_write_off,data_write_off",
     "data/sintetico/inadimplencia.csv"),

    ("sintetico", "bronze.fraudes",
     "id_fraude,cod_cliente,cod_agencia,data_ocorrencia,hora_ocorrencia,canal,tipo_fraude,dispositivo,uf_fraude,valor_fraude,flag_tentativa,flag_confirmada,valor_recuperado,data_deteccao",
     "data/sintetico/fraudes.csv"),

    # ── MACROECONOMIA ─────────────────────────────────────────────────────────
    ("externo", "bronze.ipca",
     "data,ano,mes,mes_num,indice,no_mes,acumulado_3m,acumulado_12m,acumulado_ano",
     "external_data/macroeconomia/ipca.csv"),

    ("externo", "bronze.selic",
     "data,taxa_selic",
     "external_data/macroeconomia/selic.csv"),

    ("externo", "bronze.cdi",
     "data,taxa_cdi",
     "external_data/macroeconomia/cdi.csv"),

    ("externo", "bronze.igpm",
     "data,ano,mes,mes_num,variacao_mensal,acumulado_12m",
     "external_data/macroeconomia/igpm.csv"),

    ("externo", "bronze.desemprego",
     "data,ano,trimestre,taxa_desemprego_pct",
     "external_data/macroeconomia/desemprego.csv"),

    ("externo", "bronze.dolar_ptax",
     "data,cotacao_compra,cotacao_venda,cotacao_media",
     "external_data/macroeconomia/dolar_ptax.csv"),

    ("externo", "bronze.euro_ptax",
     "data,cotacao_compra,cotacao_venda,cotacao_media",
     "external_data/macroeconomia/euro_ptax.csv"),

    # ── CALENDARIO ────────────────────────────────────────────────────────────
    ("externo", "bronze.feriados",
     "data,nome,tipo",
     "external_data/calendario/feriados.csv"),

    # ── GEOGRAFIA ─────────────────────────────────────────────────────────────
    ("externo", "bronze.municipios",
     "codigo_ibge,municipio,uf",
     "external_data/geografia/municipios.csv"),

    ("externo", "bronze.populacao",
     "codigo_ibge,municipio,ano,populacao",
     "external_data/geografia/populacao.csv"),

    ("externo", "bronze.pib_municipal",
     "codigo_ibge,municipio,ano,pib_total,pib_per_capita",
     "external_data/geografia/pib_municipal.csv"),

    ("externo", "bronze.clima_historico",
     "data,codigo_ibge,municipio,uf,temperatura_media,precipitacao_mm,vento_max_kmh",
     "external_data/clima/clima_historico.csv"),

    # ── PROJECOES ─────────────────────────────────────────────────────────────
    ("externo", "bronze.ipca_projetado",
     "data,ano,mes,mes_num,indice,no_mes,acumulado_3m,acumulado_12m,acumulado_ano,tipo",
     "external_data/projecoes/ipca_projetado.csv"),

    ("externo", "bronze.selic_projetada",
     "data,taxa_selic,tipo",
     "external_data/projecoes/selic_projetada.csv"),

    ("externo", "bronze.cdi_projetado",
     "data,taxa_cdi,tipo",
     "external_data/projecoes/cdi_projetado.csv"),

    ("externo", "bronze.populacao_projetada",
     "codigo_ibge,municipio,uf,ano,populacao,tipo",
     "external_data/projecoes/populacao_projetada.csv"),

    ("externo", "bronze.pib_projetado",
     "codigo_ibge,municipio,uf,ano,pib_total,pib_per_capita,tipo",
     "external_data/projecoes/pib_projetado.csv"),
]


# ─── Loader ──────────────────────────────────────────────────────────────────

def carregar_tabela(conn, tabela: str, colunas: str, arquivo: Path) -> int:
    if not arquivo.exists():
        print(f"  AVISO: arquivo nao encontrado, pulando: {arquivo}")
        return 0

    cols_destino = [c.strip() for c in colunas.split(",")]

    with open(arquivo, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        csv_cols = reader.fieldnames or []

        # Se o CSV tem mais colunas do que precisamos, filtramos
        precisa_filtrar = len(csv_cols) != len(cols_destino)

        if not precisa_filtrar:
            # Caminho rapido: stream direto para COPY
            f.seek(0)
            sql = f"COPY {tabela} ({colunas}) FROM STDIN CSV HEADER ENCODING 'UTF8'"
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE {tabela}")
                cur.copy_expert(sql, f)
                rowcount = cur.rowcount
        else:
            # Caminho com filtro: reescreve CSV em memoria com apenas as colunas necessarias
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(cols_destino)
            for row in reader:
                writer.writerow([row.get(csv_cols[i], "") for i in range(len(cols_destino))])
            buf.seek(0)
            sql = f"COPY {tabela} ({colunas}) FROM STDIN CSV HEADER"
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE {tabela}")
                cur.copy_expert(sql, buf)
                rowcount = cur.rowcount

    conn.commit()
    return rowcount


def main():
    parser = argparse.ArgumentParser(description="BanVic 360 -- Carga Bronze")
    parser.add_argument("--grupo", choices=["banvic", "sintetico", "externo"],
                        help="Carregar apenas um grupo especifico")
    args = parser.parse_args()

    try:
        conn = psycopg2.connect(**PG_CONN)
    except psycopg2.OperationalError as e:
        print(f"ERRO ao conectar no PostgreSQL: {e}")
        sys.exit(1)

    inicio = time.time()
    total_linhas = 0
    erros = 0

    cargas = CARGAS if not args.grupo else [c for c in CARGAS if c[0] == args.grupo]

    print(f"Iniciando carga Bronze ({len(cargas)} tabelas)...")

    for grupo, tabela, colunas, arquivo_rel in cargas:
        arquivo = ROOT / arquivo_rel
        try:
            n = carregar_tabela(conn, tabela, colunas, arquivo)
            if n > 0:
                print(f"  OK  {tabela:<45} {n:>10,} linhas")
                total_linhas += n
        except Exception as e:
            print(f"  ERRO {tabela}: {e}")
            conn.rollback()
            erros += 1

    conn.close()
    duracao = time.time() - inicio
    print(f"\nBronze concluido: {total_linhas:,} linhas em {duracao:.1f}s  |  erros: {erros}")
    sys.exit(0 if erros == 0 else 1)


if __name__ == "__main__":
    main()
