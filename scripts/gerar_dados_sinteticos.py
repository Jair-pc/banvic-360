"""
BanVic 360° — Gerador de Dados Sintéticos
==========================================
Expande o banco de dados do BanVic de ~1.000 clientes para 50.000 clientes
e de 72k transações para 3+ milhões, preservando:
  - Distribuições estatísticas dos dados reais
  - Sazonalidade mensal e anual
  - Correlações entre variáveis (renda ↔ saldo ↔ score)
  - Padrões de comportamento financeiro

Uso:
    pip install faker numpy pandas
    python scripts/gerar_dados_sinteticos.py
    python scripts/gerar_dados_sinteticos.py --etapa clientes
    python scripts/gerar_dados_sinteticos.py --etapa transacoes --ano-inicio 2024
    python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42

Etapas disponíveis:
    clientes        ->clientes_sinteticos.csv    (50.000 clientes)
    contas          ->contas_sinteticas.csv       (62.000 contas)
    transacoes      ->transacoes_sinteticas.csv   (3M+ transações)
    propostas       ->propostas_sinteticas.csv    (100k propostas)
    investimentos   ->investimentos.csv           (posições por mês)
    cartoes         ->cartoes.csv                 (faturas por mês)
    seguros         ->seguros.csv                 (apólices ativas)
    inadimplencia   ->inadimplencia.csv           (contratos em atraso)
    fraudes         ->fraudes.csv                 (ocorrências)
    tudo            ->todas as etapas
"""

import argparse
import csv
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    import numpy as np
    from faker import Faker
except ImportError:
    print("Instale: pip install faker numpy")
    sys.exit(1)

# ─── Configuração ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR     = PROJECT_ROOT / "data" / "banvic"
OUT_DIR      = PROJECT_ROOT / "data" / "sintetico"

faker_br = Faker("pt_BR")

SEED = 42

# ─── Constantes de distribuição ───────────────────────────────────────────────

# Profissões bancárias realistas (por faixa de renda)
PROFISSOES = {
    "baixa":  ["Auxiliar Administrativo", "Atendente", "Operador de Caixa",
               "Autônomo", "Motorista", "Vendedor", "Doméstica"],
    "media":  ["Analista", "Professor", "Técnico de TI", "Enfermeiro",
               "Contador", "Comerciante", "Servidor Público"],
    "alta":   ["Gerente", "Engenheiro", "Médico", "Advogado",
               "Diretor", "Empresário", "Consultor"],
}

# Escolaridade por faixa de renda
ESCOLARIDADE = {
    "baixa": ["Fundamental Incompleto", "Fundamental Completo", "Médio Incompleto"],
    "media": ["Médio Completo", "Superior Incompleto", "Superior Completo"],
    "alta":  ["Superior Completo", "Pós-graduação", "MBA", "Mestrado", "Doutorado"],
}

# Tipos de transação com peso e sinal
TIPOS_TRANSACAO = [
    ("Pix - Realizado",               0.22, -1),
    ("Pix - Recebido",                0.10, +1),
    ("Compra Crédito",                0.25, -1),
    ("Compra Débito",                 0.18, -1),
    ("TED - Realizado",               0.02, -1),
    ("TED - Recebido",                0.02, +1),
    ("Depósito em espécie",           0.06, +1),
    ("Saque",                         0.05, -1),
    ("Pagamento de boleto",           0.04, -1),
    ("DOC - Realizado",               0.01, -1),
    ("DOC - Recebido",                0.01, +1),
    ("Transferência entre CC - Débito", 0.02, -1),
    ("Transferência entre CC - Crédito",0.01, +1),
    ("Estorno de Débito",             0.01, +1),
]
TX_NOMES  = [t[0] for t in TIPOS_TRANSACAO]
TX_PESOS  = [t[1] for t in TIPOS_TRANSACAO]
TX_SINAIS = {t[0]: t[2] for t in TIPOS_TRANSACAO}

# Sazonalidade mensal (fator multiplicador de volume de transações)
SAZONALIDADE_MES = {
    1: 0.85,   # Janeiro — pós-festas
    2: 0.80,   # Fevereiro — Carnaval
    3: 0.95,
    4: 0.92,
    5: 0.95,
    6: 0.98,   # Junho — 13° adiantado PJ
    7: 0.90,   # Férias
    8: 0.95,
    9: 0.98,
    10: 1.00,
    11: 1.05,  # Black Friday
    12: 1.40,  # Natal + 13°
}

# UFs alvo e pesos de distribuição de clientes
UF_PESOS = {
    "SP": 0.30, "RJ": 0.12, "MG": 0.10, "RS": 0.07, "PR": 0.07,
    "BA": 0.05, "SC": 0.05, "PE": 0.04, "CE": 0.04, "GO": 0.03,
    "DF": 0.03, "ES": 0.02, "PA": 0.02, "AM": 0.01, "MT": 0.01,
    "MS": 0.01, "RN": 0.01, "PB": 0.01,
}

# ─── Funções auxiliares ───────────────────────────────────────────────────────

def random_date(start: date, end: date, rng: random.Random) -> date:
    delta = (end - start).days
    if delta <= 0:
        return end
    return start + timedelta(days=rng.randint(0, delta))


def gerar_cpf_valido(rng: random.Random) -> str:
    """Gera CPF com dígitos verificadores válidos (algoritmo oficial)."""
    n = [rng.randint(0, 9) for _ in range(9)]
    # Primeiro dígito
    s = sum((10 - i) * n[i] for i in range(9))
    r = 11 - (s % 11)
    n.append(0 if r >= 10 else r)
    # Segundo dígito
    s = sum((11 - i) * n[i] for i in range(10))
    r = 11 - (s % 11)
    n.append(0 if r >= 10 else r)
    return f"{''.join(map(str,n[:3]))}.{''.join(map(str,n[3:6]))}.{''.join(map(str,n[6:9]))}-{''.join(map(str,n[9:]))}"


def faixa_renda(renda: float) -> str:
    if renda < 2000:
        return "<2k"
    if renda < 5000:
        return "2-5k"
    if renda < 10000:
        return "5-10k"
    if renda < 20000:
        return "10-20k"
    return ">20k"


def faixa_etaria(idade: int) -> str:
    for upper, label in [(24, "18-24"), (34, "25-34"), (44, "35-44"),
                         (54, "45-54"), (64, "55-64")]:
        if idade <= upper:
            return label
    return "65+"


def score_from_renda(renda: float, rng: random.Random) -> int:
    """Score correlacionado com renda + ruído gaussiano."""
    base = min(900, max(200, int(renda / 30)))
    ruido = rng.gauss(0, 80)
    return max(100, min(1000, int(base + ruido)))


def faixa_score(score: int) -> str:
    if score <= 300:
        return "Muito Baixo"
    if score <= 500:
        return "Baixo"
    if score <= 700:
        return "Regular"
    if score <= 850:
        return "Bom"
    return "Excelente"


# ─── Etapa 1: Clientes ────────────────────────────────────────────────────────

def gerar_clientes(n_total: int = 50_000, seed: int = SEED) -> Path:
    rng = random.Random(seed)
    np.random.seed(seed)
    faker_br.seed_instance(seed)

    # Ler clientes reais como seed de distribuição
    with open(DATA_DIR / "clientes.csv", encoding="utf-8-sig") as f:
        reais = list(csv.DictReader(f))
    n_reais = len(reais)

    print(f"Gerando {n_total:,} clientes sintéticos (seed real: {n_reais})...")

    # Distribuição de renda: lognormal
    # Mediana ~R$3.500 (trabalhador formal brasileiro)
    rendas = np.random.lognormal(mean=8.1, sigma=0.7, size=n_total)
    rendas = np.clip(rendas, 800, 80_000)

    rows = []
    uf_list  = list(UF_PESOS.keys())
    uf_w     = list(UF_PESOS.values())

    data_inicio = date(2023, 1, 1)
    data_fim    = date(2026, 5, 31)

    for i in range(n_total):
        renda = round(rendas[i], 2)
        faixa = "baixa" if renda < 3000 else ("media" if renda < 10000 else "alta")
        uf = rng.choices(uf_list, weights=uf_w, k=1)[0]

        # Idade: distribuição real de clientes bancários (~25-65 anos)
        idade = int(np.clip(rng.gauss(40, 12), 18, 80))
        nascimento = date.today() - timedelta(days=idade * 365 + rng.randint(0, 364))

        score = score_from_renda(renda, rng)

        rows.append({
            "cod_cliente": n_reais + i + 1,
            "primeiro_nome": faker_br.first_name(),
            "ultimo_nome": faker_br.last_name(),
            "email": faker_br.email(),
            "tipo_cliente": "PF",
            "data_inclusao": random_date(data_inicio, data_fim, rng).isoformat(),
            "cpfcnpj": gerar_cpf_valido(rng),
            "data_nascimento": nascimento.isoformat(),
            "cidade": faker_br.city(),
            "uf": uf,
            "cep": faker_br.postcode(),
            "renda_mensal": renda,
            "faixa_renda": faixa_renda(renda),
            "profissao": rng.choice(PROFISSOES[faixa]),
            "escolaridade": rng.choice(ESCOLARIDADE[faixa]),
            "score_credito": score,
            "faixa_score": faixa_score(score),
            "idade": idade,
            "faixa_etaria": faixa_etaria(idade),
        })

        if (i + 1) % 10_000 == 0:
            print(f"  {i+1:,}/{n_total:,} clientes gerados")

    out = OUT_DIR / "clientes_sinteticos.csv"
    fieldnames = list(rows[0].keys())
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK clientes_sinteticos.csv ->{len(rows):,} linhas em {out}")
    return out


# ─── Etapa 2: Contas ──────────────────────────────────────────────────────────

def gerar_contas(seed: int = SEED) -> Path:
    rng = random.Random(seed + 1)
    np.random.seed(seed + 1)

    # Ler contas reais e sintéticos
    contas_reais   = list(csv.DictReader(open(DATA_DIR / "contas.csv", encoding="utf-8-sig")))
    sinteticos     = list(csv.DictReader(open(OUT_DIR / "clientes_sinteticos.csv", encoding="utf-8")))

    max_conta = max(int(c["num_conta"]) for c in contas_reais)
    max_agencia = 100  # total de agências em 2026

    print(f"Gerando contas para {len(sinteticos):,} clientes sintéticos...")

    TIPOS_CONTA = ["Corrente PF", "Poupança", "Corrente PF", "Corrente PF", "Conta Salário"]
    rows = []
    conta_id = max_conta + 1

    for cli in sinteticos:
        n_contas = 1 if rng.random() < 0.65 else (2 if rng.random() < 0.85 else 3)
        data_cli = date.fromisoformat(cli["data_inclusao"])

        for _ in range(n_contas):
            renda = float(cli["renda_mensal"])
            saldo = round(max(0, rng.gauss(renda * 2, renda * 1.5)), 2)
            data_abertura = random_date(data_cli, min(date(2026, 5, 31), data_cli + timedelta(days=90)), rng)

            rows.append({
                "num_conta": conta_id,
                "cod_cliente": cli["cod_cliente"],
                "cod_agencia": rng.randint(1, max_agencia),
                "cod_colaborador": rng.randint(1, 1200),
                "tipo_conta": rng.choice(TIPOS_CONTA),
                "data_abertura": data_abertura.isoformat(),
                "saldo_total": saldo,
                "saldo_disponivel": round(saldo * rng.uniform(0.85, 1.0), 2),
                "data_ultimo_lancamento": random_date(data_abertura, date(2026, 5, 31), rng).isoformat(),
                "flag_ativa": True,
            })
            conta_id += 1

    out = OUT_DIR / "contas_sinteticas.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK contas_sinteticas.csv ->{len(rows):,} linhas em {out}")
    return out


# ─── Etapa 3: Transações ─────────────────────────────────────────────────────

def gerar_transacoes(ano_inicio: int = 2023, ano_fim: int = 2026,
                     meta_linhas: int = 3_000_000, seed: int = SEED) -> Path:
    """
    Gera transações por bootstrapping das 72k reais + expansão proporcional.
    Preserva: tipos, distribuição de valores, sazonalidade mensal.
    """
    rng = random.Random(seed + 2)
    np.random.seed(seed + 2)

    # Ler contas para pegar num_conta disponíveis
    contas_reais  = list(csv.DictReader(open(DATA_DIR / "contas.csv", encoding="utf-8-sig")))
    contas_sint   = list(csv.DictReader(open(OUT_DIR / "contas_sinteticas.csv", encoding="utf-8")))
    todas_contas  = [int(c["num_conta"]) for c in contas_reais + contas_sint]

    print(f"Gerando ~{meta_linhas/1e6:.1f}M transações ({ano_inicio}–{ano_fim})...")

    # Ler transações reais para calibrar distribuição de valores por tipo
    tx_reais = list(csv.DictReader(open(DATA_DIR / "transacoes.csv", encoding="utf-8-sig")))
    # Calcular valor médio absoluto por tipo
    valores_por_tipo: dict = {}
    for tx in tx_reais:
        nome = tx["nome_transacao"]
        try:
            val = abs(float(tx["valor_transacao"]))
            if val > 0:
                valores_por_tipo.setdefault(nome, []).append(val)
        except ValueError:
            pass

    # Parâmetros de valor por tipo (mediana + std)
    params: dict = {}
    for nome, vals in valores_por_tipo.items():
        arr = np.array(vals)
        params[nome] = (float(np.median(arr)), float(np.std(arr) + 1))

    # Crescimento de clientes ativos por ano
    clientes_por_ano = {2023: 1_000, 2024: 5_000, 2025: 20_000, 2026: 50_000}

    rows = []
    tx_id_start = max(int(tx["cod_transacao"]) for tx in tx_reais) + 1
    tx_id = tx_id_start

    for ano in range(ano_inicio, ano_fim + 1):
        n_clientes = clientes_por_ano.get(ano, 50_000)
        # Contas ativas neste ano (amostra proporcional)
        contas_ativas = rng.sample(todas_contas, min(n_clientes, len(todas_contas)))

        for mes in range(1, 13):
            if ano == 2026 and mes > 5:  # dados até mai/2026
                break
            fator = SAZONALIDADE_MES[mes]
            tx_mes = int(n_clientes * 5 * fator)  # ~5 tx/cliente/mês baseline

            for _ in range(tx_mes):
                conta = rng.choice(contas_ativas)
                nome_tx = rng.choices(TX_NOMES, weights=TX_PESOS, k=1)[0]
                sinal = TX_SINAIS[nome_tx]
                med, std = params.get(nome_tx, (150.0, 100.0))
                valor = abs(rng.gauss(med, std))
                valor = max(1.0, min(50_000, valor))
                valor = round(valor * sinal, 2)

                dia = rng.randint(1, 28)
                hora = rng.randint(6, 23)
                minuto = rng.randint(0, 59)
                dt = datetime(ano, mes, dia, hora, minuto)

                rows.append({
                    "cod_transacao": tx_id,
                    "num_conta": conta,
                    "data_transacao": dt.isoformat(),
                    "nome_transacao": nome_tx,
                    "valor_transacao": valor,
                })
                tx_id += 1

            if len(rows) % 500_000 == 0 and len(rows) > 0:
                print(f"  {len(rows):,} transações geradas...")

    out = OUT_DIR / "transacoes_sinteticas.csv"
    fieldnames = ["cod_transacao", "num_conta", "data_transacao", "nome_transacao", "valor_transacao"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK transacoes_sinteticas.csv ->{len(rows):,} linhas em {out}")
    return out


# ─── Etapa 4: Propostas de Crédito ───────────────────────────────────────────

def gerar_propostas(seed: int = SEED) -> Path:
    rng = random.Random(seed + 3)
    np.random.seed(seed + 3)

    sinteticos = list(csv.DictReader(open(OUT_DIR / "clientes_sinteticos.csv", encoding="utf-8")))
    prop_reais = list(csv.DictReader(open(DATA_DIR / "propostas_credito.csv", encoding="utf-8-sig")))
    max_prop = max(int(p["cod_proposta"]) for p in prop_reais)

    STATUS_BY_SCORE = {
        "Muito Baixo": ["Reprovada"] * 7 + ["Em análise"] * 3,
        "Baixo":       ["Reprovada"] * 4 + ["Em análise"] * 3 + ["Aprovada"] * 3,
        "Regular":     ["Aprovada"] * 5 + ["Em análise"] * 3 + ["Reprovada"] * 2,
        "Bom":         ["Aprovada"] * 7 + ["Em análise"] * 2 + ["Enviada"] * 1,
        "Excelente":   ["Aprovada"] * 9 + ["Enviada"] * 1,
    }

    PRODUTOS = [
        ("Empréstimo Pessoal", 0.0194, 36),
        ("Crédito Consignado", 0.0060, 60),
        ("Financiamento Auto", 0.0120, 48),
        ("Financiamento Imobiliário", 0.0080, 360),
    ]

    print("Gerando propostas de crédito sintéticas...")
    rows = []
    prop_id = max_prop + 1

    for cli in sinteticos:
        # ~2 propostas por cliente em média
        n_props = rng.choices([0, 1, 2, 3, 4], weights=[0.3, 0.4, 0.2, 0.07, 0.03], k=1)[0]
        for _ in range(n_props):
            renda = float(cli["renda_mensal"])
            score_faixa = cli["faixa_score"]
            status = rng.choice(STATUS_BY_SCORE.get(score_faixa, ["Em análise"] * 5))
            produto, taxa_base, parcelas_base = rng.choice(PRODUTOS)

            # Ajuste de taxa pelo score
            multiplicador = {"Muito Baixo": 3.0, "Baixo": 2.0, "Regular": 1.3,
                             "Bom": 1.0, "Excelente": 0.7}.get(score_faixa, 1.0)
            taxa = round(taxa_base * multiplicador * rng.uniform(0.9, 1.1), 6)

            valor_prop = round(renda * rng.uniform(2, 15), 2)
            entrada = round(valor_prop * rng.uniform(0, 0.30), 2)
            financiamento = round(valor_prop - entrada, 2)
            parcelas = int(parcelas_base * rng.uniform(0.5, 1.0))
            parcela = round(financiamento * (taxa * (1+taxa)**parcelas) / ((1+taxa)**parcelas - 1), 2)

            data_entrada = random_date(
                date.fromisoformat(cli["data_inclusao"]),
                date(2026, 5, 31), rng
            )

            rows.append({
                "cod_proposta": prop_id,
                "cod_cliente": cli["cod_cliente"],
                "cod_colaborador": rng.randint(1, 1200),
                "data_entrada_proposta": data_entrada.isoformat(),
                "taxa_juros_mensal": taxa,
                "valor_proposta": valor_prop,
                "valor_financiamento": financiamento,
                "valor_entrada": entrada,
                "valor_prestacao": parcela,
                "quantidade_parcelas": parcelas,
                "carencia": rng.choice([0, 0, 0, 1, 2, 3]),
                "status_proposta": status,
                "produto": produto,
            })
            prop_id += 1

    out = OUT_DIR / "propostas_sinteticas.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK propostas_sinteticas.csv ->{len(rows):,} linhas em {out}")
    return out


# ─── Etapa 5: Investimentos ───────────────────────────────────────────────────

PRODUTOS_INVEST = [
    ("CDB_PRE",   "CDB Pré-fixado",    "CDI",     0.12,  0.14,  30,   720),
    ("CDB_CDI",   "CDB % CDI",         "CDI",     0.09,  0.115, 30,   360),
    ("LCI",       "LCI",               "CDI",     0.085, 0.105, 90,   360),
    ("LCA",       "LCA",               "CDI",     0.085, 0.105, 90,   360),
    ("FUNDO_RF",  "Fundo Renda Fixa",  "CDI",     0.09,  0.115,  1,    -1),
    ("FUNDO_MM",  "Fundo Multimercado","CDI",     0.05,  0.20,   1,    -1),
    ("FUNDO_AV",  "Fundo de Ações",    "IBOV",   -0.10,  0.40,   1,    -1),
    ("TESOURO_S", "Tesouro Selic",     "Selic",   0.10,  0.135,  1,    -1),
    ("TESOURO_I", "Tesouro IPCA+",     "IPCA+",   0.06,  0.09, 180, 3650),
    ("PREV_PGBL", "Previdência PGBL",  "CDI",     0.08,  0.12,   1,    -1),
    ("ETF_BOVA",  "ETF BOVA11",        "IBOV",   -0.10,  0.40,   1,    -1),
]

def gerar_investimentos(seed: int = SEED) -> Path:
    rng = random.Random(seed + 4)
    np.random.seed(seed + 4)

    sinteticos = list(csv.DictReader(open(OUT_DIR / "clientes_sinteticos.csv", encoding="utf-8")))
    contas_sint = list(csv.DictReader(open(OUT_DIR / "contas_sinteticas.csv", encoding="utf-8")))

    # Mapear cliente -> agência via conta
    cli_ag = {}
    for c in contas_sint:
        cli = int(c["cod_cliente"])
        if cli not in cli_ag:
            cli_ag[cli] = int(c["cod_agencia"])

    print(f"Gerando investimentos para ~{len(sinteticos)//3:,} clientes investidores...")

    rows = []
    invest_id = 1

    for cli in sinteticos:
        renda  = float(cli["renda_mensal"])
        score  = int(cli["score_credito"])
        # Probabilidade de ter investimento: maior com renda e score altos
        prob_invest = min(0.9, (renda / 20_000) * 0.6 + (score / 1000) * 0.4)
        if rng.random() > prob_invest:
            continue

        n_produtos = rng.choices([1, 2, 3], weights=[0.6, 0.3, 0.1], k=1)[0]
        produtos_escolhidos = rng.sample(PRODUTOS_INVEST, min(n_produtos, len(PRODUTOS_INVEST)))
        data_cliente = date.fromisoformat(cli["data_inclusao"])

        for (cod, nome, indexador, rent_min, rent_max, prazo_min, prazo_max) in produtos_escolhidos:
            valor_aplicado = round(renda * rng.uniform(0.5, 6.0), 2)
            valor_aplicado = max(100.0, valor_aplicado)

            data_aplic = random_date(data_cliente, date(2026, 4, 30), rng)
            if prazo_max > 0:
                prazo = rng.randint(prazo_min, min(prazo_max, 720))
                data_venc = data_aplic + timedelta(days=prazo)
            else:
                data_venc = None

            rentab = round(rng.uniform(rent_min, rent_max), 4)
            valor_atual = round(valor_aplicado * (1 + rentab), 2)

            # Status
            if data_venc and data_venc <= date(2026, 5, 31):
                status = rng.choices(["Resgatado", "Vencido"], weights=[0.7, 0.3], k=1)[0]
                data_resgate = data_venc
                valor_resgate = valor_atual
            else:
                status = "Ativo"
                data_resgate = None
                valor_resgate = None

            rows.append({
                "id_investimento":    invest_id,
                "cod_cliente":        cli["cod_cliente"],
                "cod_agencia":        cli_ag.get(int(cli["cod_cliente"]), rng.randint(1, 100)),
                "cod_produto":        cod,
                "nome_produto":       nome,
                "indexador":          indexador,
                "data_aplicacao":     data_aplic.isoformat(),
                "data_vencimento":    data_venc.isoformat() if data_venc else "",
                "valor_aplicado":     valor_aplicado,
                "valor_atual":        valor_atual,
                "rentabilidade_pct":  round(rentab * 100, 2),
                "status":             status,
                "data_resgate":       data_resgate.isoformat() if data_resgate else "",
                "valor_resgate":      valor_resgate if valor_resgate else "",
            })
            invest_id += 1

    out = OUT_DIR / "investimentos.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    patrimonio = sum(float(r["valor_atual"]) for r in rows if r["status"] == "Ativo")
    print(f"OK investimentos.csv ->{len(rows):,} posições | patrimônio ativo: R${patrimonio:,.0f}")
    return out


# ─── Etapa 6: Cartões ─────────────────────────────────────────────────────────

def gerar_cartoes(seed: int = SEED) -> Path:
    rng = random.Random(seed + 5)
    np.random.seed(seed + 5)

    sinteticos = list(csv.DictReader(open(OUT_DIR / "clientes_sinteticos.csv", encoding="utf-8")))
    contas_sint = list(csv.DictReader(open(OUT_DIR / "contas_sinteticas.csv", encoding="utf-8")))

    cli_ag = {}
    for c in contas_sint:
        cli = int(c["cod_cliente"])
        if cli not in cli_ag:
            cli_ag[cli] = int(c["cod_agencia"])

    TIPOS_CARTAO = [
        ("CART_CRED_BASIC", "Cartão Crédito Básico",   0.0299, 0.0399, 1_000,  5_000),
        ("CART_CRED_GOLD",  "Cartão Crédito Gold",     0.0249, 0.0299, 5_000, 15_000),
        ("CART_CRED_PLAT",  "Cartão Crédito Platinum", 0.0199, 0.0249,15_000, 50_000),
    ]

    print(f"Gerando faturas de cartões (2023-2026)...")

    rows = []
    fatura_id = 1

    for cli in sinteticos:
        renda  = float(cli["renda_mensal"])
        score  = int(cli["score_credito"])
        prob_cartao = min(0.95, 0.4 + (score / 1000) * 0.5)
        if rng.random() > prob_cartao:
            continue

        # Escolher tipo de cartão baseado na renda
        if renda < 3000:
            tipo_cartao = TIPOS_CARTAO[0]
        elif renda < 10000:
            tipo_cartao = rng.choices(TIPOS_CARTAO[:2], weights=[0.6, 0.4], k=1)[0]
        else:
            tipo_cartao = rng.choices(TIPOS_CARTAO, weights=[0.2, 0.4, 0.4], k=1)[0]

        cod_prod, nome_prod, taxa_rot_min, taxa_rot_max, lim_min, lim_max = tipo_cartao
        limite_total = round(renda * rng.uniform(2, 5), -2)
        limite_total = max(lim_min, min(lim_max, limite_total))
        taxa_rotativo = round(rng.uniform(taxa_rot_min, taxa_rot_max), 4)

        data_cli = date.fromisoformat(cli["data_inclusao"])

        # Gerar uma fatura por mês desde a abertura da conta
        mes_atual = date(data_cli.year, data_cli.month, 1)
        mes_fim   = date(2026, 5, 1)

        while mes_atual <= mes_fim:
            # Gastos: % do limite baseado no score (score alto ->menos uso relativo)
            pct_uso = rng.uniform(0.1, 0.9) * (1 - score / 2000)
            pct_uso = max(0.05, min(0.95, pct_uso))
            gasto = round(limite_total * pct_uso, 2)
            valor_fatura = gasto

            # Pagamento
            if rng.random() < 0.75:      # 75% pagam total
                valor_pago = valor_fatura
                valor_parcelado = 0.0
                qtd_parcelas = 0
                dias_atraso = 0
            elif rng.random() < 0.60:    # parcelamento rotativo
                valor_pago = round(valor_fatura * rng.uniform(0.3, 0.8), 2)
                valor_parcelado = valor_fatura - valor_pago
                qtd_parcelas = rng.randint(2, 12)
                dias_atraso = 0
            else:                         # inadimplência
                valor_pago = round(valor_fatura * rng.uniform(0.0, 0.3), 2)
                valor_parcelado = 0.0
                qtd_parcelas = 0
                dias_atraso = rng.randint(1, 120)

            rows.append({
                "id_fatura":           fatura_id,
                "cod_cliente":         cli["cod_cliente"],
                "cod_agencia":         cli_ag.get(int(cli["cod_cliente"]), rng.randint(1, 100)),
                "cod_produto":         cod_prod,
                "nome_produto":        nome_prod,
                "mes_referencia":      mes_atual.isoformat(),
                "limite_total":        limite_total,
                "limite_disponivel":   round(limite_total - gasto, 2),
                "gasto_mes":           gasto,
                "valor_fatura":        valor_fatura,
                "valor_pago":          valor_pago,
                "valor_parcelado":     valor_parcelado,
                "qtd_parcelas":        qtd_parcelas,
                "dias_atraso":         dias_atraso,
                "taxa_rotativo_mes":   taxa_rotativo,
                "pct_utilizacao":      round(pct_uso * 100, 1),
            })
            fatura_id += 1

            # Próximo mês
            if mes_atual.month == 12:
                mes_atual = date(mes_atual.year + 1, 1, 1)
            else:
                mes_atual = date(mes_atual.year, mes_atual.month + 1, 1)

    out = OUT_DIR / "cartoes.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"OK cartoes.csv ->{len(rows):,} faturas")
    return out


# ─── Etapa 7: Seguros ─────────────────────────────────────────────────────────

PRODUTOS_SEGURO = [
    ("SEG_VIDA", "Seguro de Vida",     50,   500,  100_000, 1_000_000, 0.02),
    ("SEG_AUTO", "Seguro Auto",        300, 1500,   30_000,   200_000, 0.05),
    ("SEG_RESI", "Seguro Residencial", 80,  400,    50_000,   500_000, 0.03),
    ("SEG_EMPR", "Seguro Empresarial", 500,5000,  200_000, 5_000_000, 0.04),
]

def gerar_seguros(seed: int = SEED) -> Path:
    rng = random.Random(seed + 6)
    np.random.seed(seed + 6)

    sinteticos = list(csv.DictReader(open(OUT_DIR / "clientes_sinteticos.csv", encoding="utf-8")))
    contas_sint = list(csv.DictReader(open(OUT_DIR / "contas_sinteticas.csv", encoding="utf-8")))

    cli_ag = {}
    for c in contas_sint:
        cli = int(c["cod_cliente"])
        if cli not in cli_ag:
            cli_ag[cli] = int(c["cod_agencia"])

    print("Gerando apólices de seguro...")

    rows = []
    apolice_id = 1

    for cli in sinteticos:
        renda = float(cli["renda_mensal"])
        prob_seguro = min(0.70, 0.15 + (renda / 30_000) * 0.55)
        if rng.random() > prob_seguro:
            continue

        # Quais seguros contratar
        seguros_comprados = [s for s in PRODUTOS_SEGURO if rng.random() < 0.35]
        if not seguros_comprados:
            seguros_comprados = [PRODUTOS_SEGURO[0]]  # ao menos vida

        data_cli = date.fromisoformat(cli["data_inclusao"])

        for (cod, nome, premio_min, premio_max, seg_min, seg_max, prob_sinistro) in seguros_comprados:
            data_inicio = random_date(data_cli, date(2026, 3, 31), rng)
            prazo_meses = rng.choices([12, 24, 36], weights=[0.5, 0.3, 0.2], k=1)[0]
            data_fim = date(
                data_inicio.year + (data_inicio.month + prazo_meses - 1) // 12,
                ((data_inicio.month + prazo_meses - 1) % 12) + 1,
                1
            )

            premio = round(rng.uniform(premio_min, min(premio_max, premio_min * renda / 3000)), 2)
            valor_segurado = round(renda * rng.uniform(10, 30), -3)
            valor_segurado = max(seg_min, min(seg_max, valor_segurado))

            # Sinistro?
            sinistro = round(valor_segurado * rng.uniform(0.05, 0.8), 2) if rng.random() < prob_sinistro else 0.0

            # Status
            if data_fim <= date(2026, 5, 31):
                status = rng.choices(["Cancelada", "Vencida"], weights=[0.3, 0.7], k=1)[0]
            else:
                status = "Ativa" if sinistro == 0 else "Sinistrada"

            foi_cross = rng.random() < 0.25  # 25% foram cross-sell

            rows.append({
                "id_apolice":        apolice_id,
                "num_apolice":       f"AP{apolice_id:08d}",
                "cod_cliente":       cli["cod_cliente"],
                "cod_agencia":       cli_ag.get(int(cli["cod_cliente"]), rng.randint(1, 100)),
                "cod_produto":       cod,
                "nome_produto":      nome,
                "data_inicio":       data_inicio.isoformat(),
                "data_fim":          data_fim.isoformat(),
                "valor_segurado":    valor_segurado,
                "premio_mensal":     premio,
                "valor_sinistro":    sinistro,
                "status_apolice":    status,
                "motivo_cancelamento": "Inadimplência" if status == "Cancelada" and rng.random() < 0.5 else ("Solicitação cliente" if status == "Cancelada" else ""),
                "foi_cross_sell":    foi_cross,
            })
            apolice_id += 1

    out = OUT_DIR / "seguros.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    ativas = sum(1 for r in rows if r["status_apolice"] == "Ativa")
    receita = sum(float(r["premio_mensal"]) for r in rows if r["status_apolice"] == "Ativa")
    print(f"OK seguros.csv ->{len(rows):,} apólices | ativas: {ativas:,} | prêmio mensal: R${receita:,.0f}")
    return out


# ─── Etapa 8: Inadimplência ───────────────────────────────────────────────────

def gerar_inadimplencia(seed: int = SEED) -> Path:
    rng = random.Random(seed + 7)
    np.random.seed(seed + 7)

    propostas = list(csv.DictReader(open(DATA_DIR / "propostas_credito.csv", encoding="utf-8-sig")))
    sint_props = list(csv.DictReader(open(OUT_DIR / "propostas_sinteticas.csv", encoding="utf-8")))
    todas_propostas = propostas + sint_props

    print(f"Gerando inadimplência a partir de {len(todas_propostas):,} propostas...")

    rows = []
    inad_id = 1

    for prop in todas_propostas:
        status = prop.get("status_proposta", "")
        if status != "Aprovada":
            continue

        # Probabilidade de inadimplência por faixa de score (inferida)
        prob_inad_map = {"Muito Baixo": 0.40, "Baixo": 0.25, "Regular": 0.12, "Bom": 0.06, "Excelente": 0.02}
        prob_inad = prob_inad_map.get(prop.get("faixa_score", "Regular"), 0.12)

        if rng.random() > prob_inad:
            continue

        valor_contrato = float(prop.get("valor_proposta", 10000))
        pct_aberto = rng.uniform(0.05, 0.90)
        valor_aberto = round(valor_contrato * pct_aberto, 2)
        dias_atraso  = rng.randint(1, 730)

        if dias_atraso <= 30:
            bucket = "0-30"
        elif dias_atraso <= 60:
            bucket = "31-60"
        elif dias_atraso <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        score = rng.randint(100, 500)
        faixa_risco = "Crítico" if dias_atraso > 180 else ("Alto" if dias_atraso > 90 else ("Médio" if dias_atraso > 30 else "Baixo"))

        valor_recuperado = round(valor_aberto * rng.uniform(0, 0.40), 2) if dias_atraso > 90 else 0.0
        write_off = dias_atraso > 360 and rng.random() < 0.5

        data_ref = date(2023 + rng.randint(0, 2), rng.randint(1, 12), 1)

        rows.append({
            "id_inadimplencia":     inad_id,
            "cod_contrato":         prop.get("cod_proposta", f"C{inad_id}"),
            "tipo_contrato":        prop.get("produto", "Empréstimo Pessoal"),
            "cod_cliente":          prop.get("cod_cliente", ""),
            "data_referencia":      data_ref.isoformat(),
            "valor_total_contrato": valor_contrato,
            "valor_aberto":         valor_aberto,
            "dias_atraso":          dias_atraso,
            "bucket":               bucket,
            "score_credito":        score,
            "faixa_risco":          faixa_risco,
            "valor_recuperado":     valor_recuperado,
            "flag_write_off":       write_off,
            "data_write_off":       (data_ref + timedelta(days=rng.randint(30, 180))).isoformat() if write_off else "",
        })
        inad_id += 1

    out = OUT_DIR / "inadimplencia.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    npl = sum(float(r["valor_aberto"]) for r in rows)
    print(f"OK inadimplencia.csv ->{len(rows):,} contratos em atraso | carteira: R${npl:,.0f}")
    return out


# ─── Etapa 9: Fraudes ─────────────────────────────────────────────────────────

TIPOS_FRAUDE = [
    "Phishing",
    "Clonagem de cartão",
    "Engenharia social",
    "Invasão de conta",
    "Fraude no PIX",
    "Boleto falso",
    "SIM swap",
]

DISPOSITIVOS = ["Mobile", "Desktop", "ATM", "POS", "Agência"]

def gerar_fraudes(seed: int = SEED) -> Path:
    rng = random.Random(seed + 8)
    np.random.seed(seed + 8)

    sinteticos = list(csv.DictReader(open(OUT_DIR / "clientes_sinteticos.csv", encoding="utf-8")))
    contas_sint = list(csv.DictReader(open(OUT_DIR / "contas_sinteticas.csv", encoding="utf-8")))

    cli_uf = {int(c["cod_cliente"]): c["uf"] for c in sinteticos}
    cli_ag = {}
    for c in contas_sint:
        cli = int(c["cod_cliente"])
        if cli not in cli_ag:
            cli_ag[cli] = int(c["cod_agencia"])

    print("Gerando ocorrências de fraude...")

    # Taxa de fraude: ~0.8% dos clientes por ano
    n_fraudes_alvo = int(len(sinteticos) * 0.008 * 3.5)  # 3.5 anos de dados

    rows = []
    fraude_id = 1
    clientes_amostrados = rng.choices(sinteticos, k=n_fraudes_alvo)

    canais_fraude = ["Pix - Realizado", "Compra Crédito", "TED - Realizado", "Depósito em espécie", "Saque"]

    for cli in clientes_amostrados:
        cod_cli = int(cli["cod_cliente"])
        uf_cli  = cli_uf.get(cod_cli, "SP")

        # Data aleatória 2023-2026
        data_fraude = random_date(date(2023, 1, 1), date(2026, 5, 31), rng)
        hora = rng.randint(0, 23)
        minuto = rng.randint(0, 59)
        hora_str = f"{hora:02d}:{minuto:02d}:00"

        # Valor: geralmente acima do ticket médio (fraudes maiores)
        valor = round(abs(rng.gauss(2500, 3000)), 2)
        valor = max(50.0, min(100_000.0, valor))

        tipo_fraude = rng.choice(TIPOS_FRAUDE)
        dispositivo = rng.choice(DISPOSITIVOS)
        canal = rng.choice(canais_fraude)

        # 65% tentativas, 35% confirmadas
        confirmada = rng.random() < 0.35
        valor_recuperado = round(valor * rng.uniform(0.3, 0.9), 2) if confirmada and rng.random() < 0.4 else 0.0

        rows.append({
            "id_fraude":              fraude_id,
            "cod_cliente":            cod_cli,
            "cod_agencia":            cli_ag.get(cod_cli, rng.randint(1, 100)),
            "data_ocorrencia":        data_fraude.isoformat(),
            "hora_ocorrencia":        hora_str,
            "canal":                  canal,
            "tipo_fraude":            tipo_fraude,
            "dispositivo":            dispositivo,
            "uf_fraude":              uf_cli,
            "valor_fraude":           valor,
            "flag_tentativa":         not confirmada,
            "flag_confirmada":        confirmada,
            "valor_recuperado":       valor_recuperado,
            "data_deteccao":          (data_fraude + timedelta(hours=rng.randint(0, 72))).isoformat(),
        })
        fraude_id += 1

    out = OUT_DIR / "fraudes.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    confirmadas = sum(1 for r in rows if r["flag_confirmada"])
    valor_total  = sum(float(r["valor_fraude"]) for r in rows if r["flag_confirmada"])
    recuperado   = sum(float(r["valor_recuperado"]) for r in rows)
    print(f"OK fraudes.csv ->{len(rows):,} ocorrências | confirmadas: {confirmadas:,} | valor: R${valor_total:,.0f} | recuperado: R${recuperado:,.0f}")
    return out


# ─── Entry point ─────────────────────────────────────────────────────────────

ETAPAS = {
    "clientes":      lambda seed: gerar_clientes(seed=seed),
    "contas":        lambda seed: gerar_contas(seed=seed),
    "transacoes":    lambda seed: gerar_transacoes(seed=seed),
    "propostas":     lambda seed: gerar_propostas(seed=seed),
    "investimentos": lambda seed: gerar_investimentos(seed=seed),
    "cartoes":       lambda seed: gerar_cartoes(seed=seed),
    "seguros":       lambda seed: gerar_seguros(seed=seed),
    "inadimplencia": lambda seed: gerar_inadimplencia(seed=seed),
    "fraudes":       lambda seed: gerar_fraudes(seed=seed),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="BanVic — Gerador de dados sintéticos")
    parser.add_argument("--etapa", choices=list(ETAPAS) + ["tudo"], default="tudo")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--ano-inicio", type=int, default=2023)
    parser.add_argument("--ano-fim", type=int, default=2026)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.etapa == "tudo":
        # Ordem importa: clientes ->contas ->transacoes ->propostas ->restante
        for nome, fn in ETAPAS.items():
            print(f"\n{'='*60}")
            print(f"Etapa: {nome.upper()}")
            print(f"{'='*60}")
            fn(args.seed)
    else:
        ETAPAS[args.etapa](args.seed)

    print(f"\nOK Concluído. Arquivos em: {OUT_DIR}")


if __name__ == "__main__":
    main()
