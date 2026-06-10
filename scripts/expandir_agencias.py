"""
BanVic 360° — Expansão de Agências
====================================
Gera 100 agências distribuídas pelo Brasil (2023-2026).

Crescimento histórico:
  2023: 10 agências (originais)
  2024: 20 agências (+10 novas)
  2025: 50 agências (+30 novas)
  2026: 100 agências (+50 novas)

Saída: data/sintetico/agencias_expandidas.csv
       (inclui as 10 originais + 90 novas = 100 total)

Uso:
    python scripts/expandir_agencias.py
"""

import csv
import os
import random
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR     = PROJECT_ROOT / "data" / "banvic"
OUT_DIR      = PROJECT_ROOT / "data" / "sintetico"

# ─── 90 novas agências: (cod, nome, cidade, uf, regiao, lat, lon, tipo) ──────

NOVAS_AGENCIAS = [
    # ── NORTE (10) ──────────────────────────────────────────────────────────
    (11, "Agência Manaus Centro",        "Manaus",           "AM", "Norte",       -3.1190, -60.0217, "Física"),
    (12, "Agência Belém",                "Belém",            "PA", "Norte",       -1.4558, -48.5044, "Física"),
    (13, "Agência Porto Velho",          "Porto Velho",      "RO", "Norte",       -8.7612, -63.9004, "Física"),
    (14, "Agência Palmas",               "Palmas",           "TO", "Norte",      -10.2491, -48.3243, "Física"),
    (15, "Agência Macapá",               "Macapá",           "AP", "Norte",        0.0349, -51.0694, "Digital"),
    (16, "Agência Boa Vista",            "Boa Vista",        "RR", "Norte",        2.8235, -60.6758, "Digital"),
    (17, "Agência Santarém",             "Santarém",         "PA", "Norte",       -2.4448, -54.7086, "Física"),
    (18, "Agência Marabá",               "Marabá",           "PA", "Norte",       -5.3686, -49.1178, "Física"),
    (19, "Agência Rio Branco",           "Rio Branco",       "AC", "Norte",       -9.9753, -67.8249, "Física"),
    (20, "Agência Ananindeua",           "Ananindeua",       "PA", "Norte",       -1.3636, -48.3724, "Digital"),

    # ── NORDESTE (19 — Recife já existe como cod 10) ─────────────────────────
    (21, "Agência Fortaleza",            "Fortaleza",        "CE", "Nordeste",    -3.7172, -38.5433, "Física"),
    (22, "Agência Fortaleza Premium",    "Fortaleza",        "CE", "Nordeste",    -3.7275, -38.4873, "Premium"),
    (23, "Agência Salvador",             "Salvador",         "BA", "Nordeste",   -12.9714, -38.5014, "Física"),
    (24, "Agência Salvador Corporate",  "Salvador",         "BA", "Nordeste",   -12.9850, -38.4736, "Corporate"),
    (25, "Agência Natal",                "Natal",            "RN", "Nordeste",    -5.7945, -35.2110, "Física"),
    (26, "Agência João Pessoa",          "João Pessoa",      "PB", "Nordeste",    -7.1195, -34.8450, "Física"),
    (27, "Agência Teresina",             "Teresina",         "PI", "Nordeste",    -5.0892, -42.8019, "Física"),
    (28, "Agência São Luís",             "São Luís",         "MA", "Nordeste",    -2.5297, -44.3028, "Física"),
    (29, "Agência Maceió",               "Maceió",           "AL", "Nordeste",    -9.6658, -35.7350, "Física"),
    (30, "Agência Aracaju",              "Aracaju",          "SE", "Nordeste",   -10.9472, -37.0731, "Física"),
    (31, "Agência Feira de Santana",     "Feira de Santana", "BA", "Nordeste",   -12.2664, -38.9663, "Física"),
    (32, "Agência Campina Grande",       "Campina Grande",   "PB", "Nordeste",    -7.2306, -35.8811, "Digital"),
    (33, "Agência Caruaru",              "Caruaru",          "PE", "Nordeste",    -8.2760, -35.9756, "Física"),
    (34, "Agência Mossoró",              "Mossoró",          "RN", "Nordeste",    -5.1878, -37.3440, "Digital"),
    (35, "Agência Juazeiro do Norte",    "Juazeiro do Norte","CE", "Nordeste",    -7.2133, -39.3150, "Física"),
    (36, "Agência Petrolina",            "Petrolina",        "PE", "Nordeste",    -9.3891, -40.5031, "Física"),
    (37, "Agência Imperatriz",           "Imperatriz",       "MA", "Nordeste",    -5.5253, -47.4742, "Digital"),
    (38, "Agência Vitória da Conquista", "Vitória da Conquista","BA","Nordeste", -14.8650, -40.8444, "Física"),
    (39, "Agência Recife Corporate",     "Recife",           "PE", "Nordeste",    -8.0522, -34.9286, "Corporate"),

    # ── CENTRO-OESTE (10) ────────────────────────────────────────────────────
    (40, "Agência Brasília",             "Brasília",         "DF", "Centro-Oeste",-15.7801, -47.9292, "Física"),
    (41, "Agência Brasília Premium",     "Brasília",         "DF", "Centro-Oeste",-15.8267, -47.9218, "Premium"),
    (42, "Agência Brasília Corporate",   "Brasília",         "DF", "Centro-Oeste",-15.7998, -47.8645, "Corporate"),
    (43, "Agência Goiânia",              "Goiânia",          "GO", "Centro-Oeste",-16.6869, -49.2648, "Física"),
    (44, "Agência Goiânia Norte",        "Goiânia",          "GO", "Centro-Oeste",-16.5975, -49.2752, "Física"),
    (45, "Agência Cuiabá",               "Cuiabá",           "MT", "Centro-Oeste",-15.6010, -56.0979, "Física"),
    (46, "Agência Campo Grande",         "Campo Grande",     "MS", "Centro-Oeste",-20.4697, -54.6201, "Física"),
    (47, "Agência Anápolis",             "Anápolis",         "GO", "Centro-Oeste",-16.3281, -48.9528, "Digital"),
    (48, "Agência Rondonópolis",         "Rondonópolis",     "MT", "Centro-Oeste",-16.4735, -54.6356, "Digital"),
    (49, "Agência Dourados",             "Dourados",         "MS", "Centro-Oeste",-22.2211, -54.8056, "Física"),

    # ── SUDESTE (33) — SP(6) e RJ(1) já existem ──────────────────────────────
    # Minas Gerais (12)
    (50, "Agência Belo Horizonte",       "Belo Horizonte",   "MG", "Sudeste",    -19.9167, -43.9345, "Física"),
    (51, "Agência BH Savassi",           "Belo Horizonte",   "MG", "Sudeste",    -19.9389, -43.9339, "Premium"),
    (52, "Agência BH Corporate",         "Belo Horizonte",   "MG", "Sudeste",    -19.9200, -43.9543, "Corporate"),
    (53, "Agência Contagem",             "Contagem",         "MG", "Sudeste",    -19.9317, -44.0536, "Física"),
    (54, "Agência Uberlândia",           "Uberlândia",       "MG", "Sudeste",    -18.9188, -48.2773, "Física"),
    (55, "Agência Juiz de Fora",         "Juiz de Fora",     "MG", "Sudeste",    -21.7642, -43.3503, "Física"),
    (56, "Agência Betim",                "Betim",            "MG", "Sudeste",    -19.9675, -44.1984, "Física"),
    (57, "Agência Montes Claros",        "Montes Claros",    "MG", "Sudeste",    -16.7281, -43.8647, "Física"),
    (58, "Agência Uberaba",              "Uberaba",          "MG", "Sudeste",    -19.7482, -47.9317, "Física"),
    (59, "Agência Governador Valadares", "Gov. Valadares",   "MG", "Sudeste",    -18.8539, -41.9494, "Física"),
    (60, "Agência Ipatinga",             "Ipatinga",         "MG", "Sudeste",    -19.4681, -42.5381, "Física"),
    (61, "Agência Sete Lagoas",          "Sete Lagoas",      "MG", "Sudeste",    -19.4681, -44.2472, "Digital"),
    # Espírito Santo (3)
    (62, "Agência Vitória",              "Vitória",          "ES", "Sudeste",    -20.2976, -40.2958, "Física"),
    (63, "Agência Vila Velha",           "Vila Velha",       "ES", "Sudeste",    -20.3297, -40.2922, "Física"),
    (64, "Agência Serra",                "Serra",            "ES", "Sudeste",    -20.1283, -40.3097, "Digital"),
    # São Paulo - novas (12)
    (65, "Agência Ribeirão Preto",       "Ribeirão Preto",   "SP", "Sudeste",    -21.1767, -47.8208, "Física"),
    (66, "Agência Santos",               "Santos",           "SP", "Sudeste",    -23.9608, -46.3336, "Física"),
    (67, "Agência São José dos Campos",  "São José dos Campos","SP","Sudeste",   -23.1896, -45.8841, "Física"),
    (68, "Agência Guarulhos",            "Guarulhos",        "SP", "Sudeste",    -23.4628, -46.5333, "Física"),
    (69, "Agência São Bernardo",         "São Bernardo do Campo","SP","Sudeste", -23.6939, -46.5650, "Física"),
    (70, "Agência Sorocaba",             "Sorocaba",         "SP", "Sudeste",    -23.5015, -47.4526, "Física"),
    (71, "Agência Mogi das Cruzes",      "Mogi das Cruzes",  "SP", "Sudeste",    -23.5220, -46.1878, "Digital"),
    (72, "Agência Jundiaí",              "Jundiaí",          "SP", "Sudeste",    -23.1858, -46.8839, "Física"),
    (73, "Agência Piracicaba",           "Piracicaba",       "SP", "Sudeste",    -22.7253, -47.6492, "Física"),
    (74, "Agência São José do Rio Preto","São José do Rio Preto","SP","Sudeste", -20.8197, -49.3794, "Física"),
    (75, "Agência Barueri",              "Barueri",          "SP", "Sudeste",    -23.5042, -46.8764, "Corporate"),
    (76, "Agência Franca",               "Franca",           "SP", "Sudeste",    -20.5386, -47.4008, "Física"),
    # Rio de Janeiro - novas (6)
    (77, "Agência Niterói",              "Niterói",          "RJ", "Sudeste",    -22.8833, -43.1033, "Física"),
    (78, "Agência Duque de Caxias",      "Duque de Caxias",  "RJ", "Sudeste",    -22.7856, -43.3117, "Física"),
    (79, "Agência Nova Iguaçu",          "Nova Iguaçu",      "RJ", "Sudeste",    -22.7592, -43.4511, "Física"),
    (80, "Agência São Gonçalo",          "São Gonçalo",      "RJ", "Sudeste",    -22.8269, -43.0539, "Física"),
    (81, "Agência RJ Barra da Tijuca",   "Rio de Janeiro",   "RJ", "Sudeste",    -23.0006, -43.3656, "Premium"),
    (82, "Agência RJ Corporate",         "Rio de Janeiro",   "RJ", "Sudeste",    -22.9083, -43.1764, "Corporate"),

    # ── SUL (18) — RS(1) e SC(1) já existem ──────────────────────────────────
    # Paraná (10)
    (83, "Agência Curitiba",             "Curitiba",         "PR", "Sul",        -25.4284, -49.2733, "Física"),
    (84, "Agência Curitiba Batel",       "Curitiba",         "PR", "Sul",        -25.4439, -49.2889, "Premium"),
    (85, "Agência Curitiba Corporate",   "Curitiba",         "PR", "Sul",        -25.4156, -49.2386, "Corporate"),
    (86, "Agência Londrina",             "Londrina",         "PR", "Sul",        -23.3045, -51.1696, "Física"),
    (87, "Agência Maringá",              "Maringá",          "PR", "Sul",        -23.4205, -51.9333, "Física"),
    (88, "Agência Ponta Grossa",         "Ponta Grossa",     "PR", "Sul",        -25.0944, -50.1619, "Física"),
    (89, "Agência Cascavel",             "Cascavel",         "PR", "Sul",        -24.9578, -53.4596, "Física"),
    (90, "Agência Foz do Iguaçu",        "Foz do Iguaçu",    "PR", "Sul",        -25.5469, -54.5882, "Física"),
    (91, "Agência Colombo",              "Colombo",          "PR", "Sul",        -25.2925, -49.2233, "Digital"),
    (92, "Agência Apucarana",            "Apucarana",        "PR", "Sul",        -23.5503, -51.4611, "Digital"),
    # Santa Catarina - novas (5)
    (93, "Agência Joinville",            "Joinville",        "SC", "Sul",        -26.3044, -48.8489, "Física"),
    (94, "Agência Blumenau",             "Blumenau",         "SC", "Sul",        -26.9194, -49.0661, "Física"),
    (95, "Agência Criciúma",             "Criciúma",         "SC", "Sul",        -28.6781, -49.3697, "Física"),
    (96, "Agência Chapecó",              "Chapecó",          "SC", "Sul",        -27.1006, -52.6152, "Física"),
    (97, "Agência São José SC",          "São José",         "SC", "Sul",        -27.5606, -48.6347, "Digital"),
    # Rio Grande do Sul - novas (3)
    (98, "Agência Caxias do Sul",        "Caxias do Sul",    "RS", "Sul",        -29.1678, -51.1794, "Física"),
    (99, "Agência Canoas",               "Canoas",           "RS", "Sul",        -29.9178, -51.1839, "Física"),
    (100,"Agência Pelotas",              "Pelotas",          "RS", "Sul",        -31.7654, -52.3376, "Física"),
]

# Metas comerciais mensais por tipo (R$)
META_POR_TIPO = {
    "Física":    500_000,
    "Digital":   300_000,
    "Premium":  2_000_000,
    "Corporate": 5_000_000,
}

# Variação aleatória na meta (±20%)
META_VARIACAO = 0.20

# Timeline de abertura: quais agências abrem em cada ano
# 10 existentes: 2010-2021 (mantidas)
# 11-20: abrem em 2024 (total 20)
# 21-50: abrem em 2025 (total 50)
# 51-100: abrem em 2026 (total 100)
def ano_abertura(cod: int) -> int:
    if cod <= 20:
        return 2024
    if cod <= 50:
        return 2025
    return 2026


def data_abertura_aleatoria(ano: int, rng: random.Random) -> date:
    inicio = date(ano, 1, 1)
    fim    = date(ano, 12, 31)
    delta  = (fim - inicio).days
    return inicio + timedelta(days=rng.randint(0, delta))


def formatar_endereco(cidade: str, uf: str) -> str:
    """Gera endereço genérico realista."""
    logradouros = [
        "Av. Brasil", "Av. Paulista", "Av. Rio Branco", "Rua das Flores",
        "Av. Independência", "Rua Marechal Deodoro", "Av. Getúlio Vargas",
        "Av. Sete de Setembro", "Rua XV de Novembro", "Av. Dom Pedro II",
    ]
    rua = logradouros[hash(cidade) % len(logradouros)]
    numero = (hash(cidade + uf) % 4000) + 100
    return f"{rua}, {numero} - Centro, {cidade} - {uf}"


def gerar_cep(uf: str, rng: random.Random) -> str:
    # Faixas de CEP por UF (aproximadas)
    faixas = {
        "SP": (1000000, 19999999), "RJ": (20000000, 28999999),
        "ES": (29000000, 29999999), "MG": (30000000, 39999999),
        "BA": (40000000, 48999999), "SE": (49000000, 49999999),
        "PE": (50000000, 56999999), "AL": (57000000, 57999999),
        "PB": (58000000, 58999999), "RN": (59000000, 59999999),
        "CE": (60000000, 63999999), "PI": (64000000, 64999999),
        "MA": (65000000, 65999999), "PA": (66000000, 68899999),
        "AP": (68900000, 68999999), "AM": (69000000, 69899999),
        "RR": (69300000, 69399999), "AC": (69900000, 69999999),
        "RO": (76800000, 76999999), "TO": (77000000, 77999999),
        "GO": (72800000, 76799999), "DF": (70000000, 72799999),
        "MT": (78000000, 78999999), "MS": (79000000, 79999999),
        "PR": (80000000, 87999999), "SC": (88000000, 89999999),
        "RS": (90000000, 99999999),
    }
    lo, hi = faixas.get(uf, (10000000, 99999999))
    n = rng.randint(lo, hi)
    s = f"{n:08d}"
    return f"{s[:5]}-{s[5:]}"


def main():
    rng = random.Random(42)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Ler agências originais ─────────────────────────────────────
    agencias_originais = []
    with open(DATA_DIR / "agencias.csv", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            agencias_originais.append({
                "cod_agencia":            int(row["cod_agencia"]),
                "nome":                   row["nome"],
                "tipo_agencia":           row["tipo_agencia"],
                "endereco":               row["endereco"],
                "cidade":                 row["cidade"],
                "uf":                     row["uf"],
                "cep":                    "",
                "regiao":                 _regiao_por_uf(row["uf"]),
                "data_abertura":          row["data_abertura"],
                "data_encerramento":      "",
                "eh_ativa":               True,
                "meta_comercial_mensal":  META_POR_TIPO.get(row["tipo_agencia"], 500_000),
                "latitude":               "",
                "longitude":              "",
            })

    # ── Gerar novas agências ───────────────────────────────────────
    novas = []
    for (cod, nome, cidade, uf, regiao, lat, lon, tipo) in NOVAS_AGENCIAS:
        ano = ano_abertura(cod)
        dt  = data_abertura_aleatoria(ano, rng)
        meta_base = META_POR_TIPO[tipo]
        variacao  = rng.uniform(1 - META_VARIACAO, 1 + META_VARIACAO)
        meta      = round(meta_base * variacao, -3)  # arredonda p/ milhar

        novas.append({
            "cod_agencia":            cod,
            "nome":                   nome,
            "tipo_agencia":           tipo,
            "endereco":               formatar_endereco(cidade, uf),
            "cidade":                 cidade,
            "uf":                     uf,
            "cep":                    gerar_cep(uf, rng),
            "regiao":                 regiao,
            "data_abertura":          dt.isoformat(),
            "data_encerramento":      "",
            "eh_ativa":               True,
            "meta_comercial_mensal":  int(meta),
            "latitude":               lat,
            "longitude":              lon,
        })

    todas = agencias_originais + novas
    todas.sort(key=lambda r: r["cod_agencia"])

    # ── Salvar CSV ─────────────────────────────────────────────────
    campos = [
        "cod_agencia", "nome", "tipo_agencia", "endereco", "cidade", "uf",
        "cep", "regiao", "data_abertura", "data_encerramento", "eh_ativa",
        "meta_comercial_mensal", "latitude", "longitude",
    ]
    out = OUT_DIR / "agencias_expandidas.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todas)

    # ── Resumo ─────────────────────────────────────────────────────
    print(f"Agencias geradas: {len(todas)} total ({len(agencias_originais)} originais + {len(novas)} novas)")
    print(f"Arquivo: {out}")

    contagem_regiao: dict = {}
    contagem_tipo: dict   = {}
    contagem_ano: dict    = {}
    for a in todas:
        contagem_regiao[a["regiao"]] = contagem_regiao.get(a["regiao"], 0) + 1
        contagem_tipo[a["tipo_agencia"]] = contagem_tipo.get(a["tipo_agencia"], 0) + 1
        ano = a["data_abertura"][:4]
        contagem_ano[ano] = contagem_ano.get(ano, 0) + 1

    print("\nPor regiao:")
    for r, n in sorted(contagem_regiao.items()):
        print(f"  {r:<15}: {n:>3}")

    print("\nPor tipo:")
    for t, n in sorted(contagem_tipo.items()):
        print(f"  {t:<12}: {n:>3}")

    print("\nAcumulado por ano (simulando crescimento):")
    acum = 0
    for ano in sorted(contagem_ano):
        acum += contagem_ano[ano]
        print(f"  ate {ano}: {acum:>3} agencias")


def _regiao_por_uf(uf: str) -> str:
    mapa = {
        "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte",
        "RO": "Norte", "RR": "Norte", "TO": "Norte",
        "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
        "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
        "SE": "Nordeste",
        "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste", "MT": "Centro-Oeste",
        "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
        "PR": "Sul", "RS": "Sul", "SC": "Sul",
    }
    return mapa.get(uf, "Sudeste")


if __name__ == "__main__":
    main()
