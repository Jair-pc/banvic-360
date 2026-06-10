"""
BanVic 360° — Expansão de Colaboradores
=========================================
Gera 1.200 colaboradores com hierarquia completa: cargo, departamento,
salário, data de admissão e agência de lotação.

Crescimento histórico:
  2023: 100 colaboradores (originais)
  2024: 180 colaboradores (+80)
  2025: 500 colaboradores (+320)
  2026: 1.200 colaboradores (+700)

Saída: data/sintetico/colaboradores_expandidos.csv
       (inclui os 100 originais enriquecidos + 1.100 novos = 1.200 total)

Uso:
    python scripts/expandir_colaboradores.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

try:
    from faker import Faker
    import numpy as np
except ImportError:
    print("Instale: pip install faker numpy")
    raise

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR     = PROJECT_ROOT / "data" / "banvic"
SINT_DIR     = PROJECT_ROOT / "data" / "sintetico"
OUT_DIR      = PROJECT_ROOT / "data" / "sintetico"

faker_br = Faker("pt_BR")

SEED = 42

# ─── Estrutura hierárquica ────────────────────────────────────────────────────

# (cargo, nivel, departamento, salario_base, salario_max)
CARGOS = [
    # Nível 1 — Diretoria
    ("Diretor Geral",           1, "Diretoria",      25_000, 45_000),
    ("Diretor Comercial",       1, "Comercial",      22_000, 38_000),
    ("Diretor de Crédito",      1, "Crédito",        22_000, 38_000),
    ("Diretor de Tecnologia",   1, "TI",             22_000, 38_000),
    ("Diretor Financeiro",      1, "Financeiro",     22_000, 38_000),
    # Nível 2 — Gerência
    ("Gerente de Agência",      2, "Operações",      10_000, 18_000),
    ("Gerente Comercial",       2, "Comercial",       9_000, 16_000),
    ("Gerente de Crédito",      2, "Crédito",         9_000, 16_000),
    ("Gerente de TI",           2, "TI",              9_000, 16_000),
    ("Gerente Financeiro",      2, "Financeiro",      9_000, 16_000),
    ("Gerente de RH",           2, "RH",              8_000, 14_000),
    ("Gerente de Compliance",   2, "Compliance",      9_000, 16_000),
    # Nível 3 — Analistas / Especialistas
    ("Analista de Crédito",     3, "Crédito",         5_000,  9_000),
    ("Analista Comercial",      3, "Comercial",       5_000,  9_000),
    ("Analista de TI",          3, "TI",              6_000, 11_000),
    ("Analista Financeiro",     3, "Financeiro",      5_500,  9_500),
    ("Analista de Dados",       3, "TI",              6_500, 12_000),
    ("Especialista em Seguros", 3, "Produtos",        5_500, 10_000),
    ("Especialista em Invest.", 3, "Produtos",        6_000, 11_000),
    ("Analista de Compliance",  3, "Compliance",      5_000,  9_000),
    # Nível 4 — Assistentes / Operacional
    ("Assistente Administrativo",4,"Operações",       2_500,  4_500),
    ("Assistente de Crédito",   4, "Crédito",         2_800,  4_500),
    ("Caixa",                   4, "Operações",       2_200,  3_800),
    ("Assistente Comercial",    4, "Comercial",       2_500,  4_500),
    ("Operador de Suporte TI",  4, "TI",              3_000,  5_500),
    ("Assistente de RH",        4, "RH",              2_500,  4_000),
    ("Atendente",               4, "Operações",       2_000,  3_500),
]

# Pesos de cada cargo para a distribuição final (pirâmide hierárquica)
CARGO_PESOS = [
    0.005,  # Diretor Geral
    0.004,  # Diretor Comercial
    0.004,  # Diretor de Crédito
    0.004,  # Diretor de Tecnologia
    0.004,  # Diretor Financeiro
    0.060,  # Gerente de Agência
    0.040,  # Gerente Comercial
    0.030,  # Gerente de Crédito
    0.025,  # Gerente de TI
    0.025,  # Gerente Financeiro
    0.015,  # Gerente de RH
    0.015,  # Gerente de Compliance
    0.070,  # Analista de Crédito
    0.060,  # Analista Comercial
    0.050,  # Analista de TI
    0.040,  # Analista Financeiro
    0.040,  # Analista de Dados
    0.020,  # Especialista Seguros
    0.020,  # Especialista Invest.
    0.020,  # Analista Compliance
    0.100,  # Assistente Admin
    0.060,  # Assistente Crédito
    0.080,  # Caixa
    0.059,  # Assistente Comercial
    0.040,  # Operador Suporte TI
    0.020,  # Assistente RH
    0.090,  # Atendente
]

assert abs(sum(CARGO_PESOS) - 1.0) < 0.01, "Pesos devem somar 1"

# Distribuição de colaboradores por agência (agências menores têm menos)
COLAB_POR_TIPO_AGENCIA = {
    "Física":    12,   # média de colaboradores por agência física
    "Digital":    6,
    "Premium":   15,
    "Corporate": 20,
}


def gerar_cpf_valido(rng: random.Random) -> str:
    n = [rng.randint(0, 9) for _ in range(9)]
    s = sum((10 - i) * n[i] for i in range(9))
    r = 11 - (s % 11)
    n.append(0 if r >= 10 else r)
    s = sum((11 - i) * n[i] for i in range(10))
    r = 11 - (s % 11)
    n.append(0 if r >= 10 else r)
    return f"{''.join(map(str,n[:3]))}.{''.join(map(str,n[3:6]))}.{''.join(map(str,n[6:9]))}-{''.join(map(str,n[9:]))}"


def random_date(start: date, end: date, rng: random.Random) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=rng.randint(0, delta))


def data_admissao_por_agencia(cod_agencia: int, rng: random.Random) -> date:
    """Colaborador admitido entre abertura da agência e 6 meses depois."""
    if cod_agencia <= 10:
        return random_date(date(2010, 1, 1), date(2023, 12, 31), rng)
    elif cod_agencia <= 20:
        return random_date(date(2024, 1, 1), date(2024, 12, 31), rng)
    elif cod_agencia <= 50:
        return random_date(date(2025, 1, 1), date(2025, 12, 31), rng)
    else:
        return random_date(date(2026, 1, 1), date(2026, 5, 31), rng)


def main():
    rng = random.Random(SEED)
    np.random.seed(SEED)
    faker_br.seed_instance(SEED)

    # ── Ler agências expandidas ──────────────────────────────────────
    agencias = []
    ag_path = SINT_DIR / "agencias_expandidas.csv"
    if not ag_path.exists():
        print("ERRO: Rode expandir_agencias.py primeiro.")
        return

    with open(ag_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            agencias.append({
                "cod_agencia":  int(row["cod_agencia"]),
                "tipo_agencia": row["tipo_agencia"],
                "cidade":       row["cidade"],
                "uf":           row["uf"],
                "regiao":       row["regiao"],
            })

    # ── Ler colaboradores originais (para reaproveitar cod_ e nomes) ──
    colab_originais = []
    cpfs_usados = set()
    with open(DATA_DIR / "colaboradores.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            colab_originais.append(row)
            if row.get("cpf"):
                cpfs_usados.add(row["cpf"])

    max_cod = max(int(c["cod_colaborador"]) for c in colab_originais)

    # ── Definir quantos colaboradores por agência ─────────────────────
    # Meta: ~1.200 total. Distribui proporcionalmente.
    # Agências existentes (1-10) já têm 100 colaboradores originais.
    # As novas agências (11-100) precisam de 1.100 novos.
    agencias_novas = [a for a in agencias if a["cod_agencia"] > 10]

    # Calcular cotas por agência nova
    total_pesos = sum(COLAB_POR_TIPO_AGENCIA[a["tipo_agencia"]] for a in agencias_novas)
    meta_novos  = 1_100

    cotas: list[tuple] = []
    for a in agencias_novas:
        peso = COLAB_POR_TIPO_AGENCIA[a["tipo_agencia"]]
        n    = max(1, round(meta_novos * peso / total_pesos))
        cotas.append((a, n))

    # Ajustar para atingir exatamente 1.100
    total_cotas = sum(n for _, n in cotas)
    diff = meta_novos - total_cotas
    if diff != 0:
        # Adicionar/remover do maior grupo
        idx = max(range(len(cotas)), key=lambda i: cotas[i][1])
        a, n = cotas[idx]
        cotas[idx] = (a, n + diff)

    # ── Gerar colaboradores novos ─────────────────────────────────────
    cargo_nomes  = [c[0] for c in CARGOS]
    cargos_info  = {c[0]: c for c in CARGOS}

    novos = []
    cod = max_cod + 1

    for (ag, n_colab) in cotas:
        for _ in range(n_colab):
            cargo_nome = rng.choices(cargo_nomes, weights=CARGO_PESOS, k=1)[0]
            _, nivel, dept, sal_min, sal_max = cargos_info[cargo_nome]

            salario = round(rng.uniform(sal_min, sal_max), 2)
            idade   = max(22, min(65, int(rng.gauss(38, 10))))
            dt_nasc = date.today() - timedelta(days=idade * 365 + rng.randint(0, 364))
            dt_adm  = data_admissao_por_agencia(ag["cod_agencia"], rng)

            # CPF único
            while True:
                cpf = gerar_cpf_valido(rng)
                if cpf not in cpfs_usados:
                    cpfs_usados.add(cpf)
                    break

            novos.append({
                "cod_colaborador":   cod,
                "primeiro_nome":     faker_br.first_name(),
                "ultimo_nome":       faker_br.last_name(),
                "email":             faker_br.email(),
                "cpf":               cpf,
                "data_nascimento":   dt_nasc.isoformat(),
                "cidade":            ag["cidade"],
                "uf":                ag["uf"],
                "regiao":            ag["regiao"],
                "cargo":             cargo_nome,
                "nivel_hierarquico": nivel,
                "departamento":      dept,
                "salario_base":      salario,
                "cod_agencia":       ag["cod_agencia"],
                "data_admissao":     dt_adm.isoformat(),
                "data_demissao":     "",
                "eh_ativo":          True,
            })
            cod += 1

    # ── Enriquecer originais (adicionar campos que faltavam) ──────────
    originais_enriquecidos = []
    for i, c in enumerate(colab_originais):
        cargo_nome = rng.choices(cargo_nomes, weights=CARGO_PESOS, k=1)[0]
        _, nivel, dept, sal_min, sal_max = cargos_info[cargo_nome]
        # Agências 1-10 para os originais
        ag_idx = i % 10
        ag_orig = agencias[ag_idx]

        originais_enriquecidos.append({
            "cod_colaborador":   c["cod_colaborador"],
            "primeiro_nome":     c.get("primeiro_nome", c.get("cod_colaborador", "")),
            "ultimo_nome":       c.get("ultimo_nome", ""),
            "email":             c.get("email", ""),
            "cpf":               c.get("cpf", ""),
            "data_nascimento":   c.get("data_nascimento", ""),
            "cidade":            ag_orig["cidade"],
            "uf":                ag_orig["uf"],
            "regiao":            ag_orig["regiao"],
            "cargo":             cargo_nome,
            "nivel_hierarquico": nivel,
            "departamento":      dept,
            "salario_base":      round(rng.uniform(sal_min, sal_max), 2),
            "cod_agencia":       ag_orig["cod_agencia"],
            "data_admissao":     random_date(date(2010, 1, 1), date(2023, 12, 31), rng).isoformat(),
            "data_demissao":     "",
            "eh_ativo":          True,
        })

    todos = originais_enriquecidos + novos
    todos.sort(key=lambda r: int(r["cod_colaborador"]))

    # ── Salvar ────────────────────────────────────────────────────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    campos = [
        "cod_colaborador", "primeiro_nome", "ultimo_nome", "email", "cpf",
        "data_nascimento", "cidade", "uf", "regiao", "cargo",
        "nivel_hierarquico", "departamento", "salario_base",
        "cod_agencia", "data_admissao", "data_demissao", "eh_ativo",
    ]
    out = OUT_DIR / "colaboradores_expandidos.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todos)

    print(f"Colaboradores gerados: {len(todos)} total ({len(originais_enriquecidos)} originais + {len(novos)} novos)")
    print(f"Arquivo: {out}")

    # Resumo por nivel
    niveis = {}
    for c in todos:
        n = c["nivel_hierarquico"]
        niveis[n] = niveis.get(n, 0) + 1
    labels = {1: "Diretoria", 2: "Gerencia", 3: "Analistas", 4: "Operacional"}
    print("\nPor nivel hierarquico:")
    for n in sorted(niveis):
        print(f"  Nivel {n} ({labels[n]:<12}): {niveis[n]:>4}")

    print(f"\nMeta 1.200: {'OK' if len(todos) >= 1180 else 'VERIFICAR'} ({len(todos)} gerados)")


if __name__ == "__main__":
    main()
