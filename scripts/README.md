# Scripts — BanVic 360

Esta pasta contém os scripts Python que fazem o trabalho pesado do projeto: baixar dados, gerar dados fictícios, carregar no banco e verificar se as respostas estão corretas.

Pense neles como ferramentas de uma caixa: cada uma tem uma função específica, e você as usa na ordem certa.

---

## Visão Geral

| Script | O que faz | Quando rodar |
|---|---|---|
| `download_datasets.py` | Baixa 14 datasets públicos (BCB, IBGE, clima) | Uma vez, no início |
| `expandir_agencias.py` | Cria 100 agências distribuídas pelo Brasil | Uma vez, no início |
| `expandir_colaboradores.py` | Cria 1.200 funcionários com cargos e salários | Uma vez, após as agências |
| `gerar_dados_sinteticos.py` | Gera 50k clientes, 70k contas, 3M+ transações | Uma vez, no início |
| `projetar_series_historicas.py` | Extende dados de IPCA, Selic e PIB até 2026 | Uma vez, no início |
| `entrypoint.py` | Roda o pipeline inteiro de ponta a ponta | Quando quiser recriar tudo |
| `carga_bronze.py` | Carrega os CSVs no banco PostgreSQL | Antes de rodar qualquer projeto |
| `validar_gabarito.py` | Calcula as 8 respostas dos dados originais (sem banco) | Para gerar o gabarito |
| `gerar_gabarito_gold.py` | Gera o gabarito a partir do banco PostgreSQL | Após o Projeto 1 estar completo |
| `validar_gabarito_pg.py` | Verifica se o banco chegou nas respostas corretas | Para validar qualquer projeto |

---

## Grupo 1 — Preparação de Dados

Esses scripts criam o material de trabalho. Rode **uma vez**, nessa ordem, antes de começar qualquer projeto.

### `download_datasets.py`

Baixa dados reais do governo brasileiro:
- Taxa Selic, CDI, IPCA, câmbio (Banco Central do Brasil)
- Municípios, população, PIB por cidade (IBGE)
- Feriados nacionais (BrasilAPI)
- Temperatura e chuva de 100 cidades (Open-Meteo)

```bash
# Baixar tudo
python scripts/download_datasets.py

# Baixar só um dataset específico
python scripts/download_datasets.py --dataset ipca
python scripts/download_datasets.py --dataset selic
python scripts/download_datasets.py --dataset clima
```

Salva em `external_data/`.

---

### `expandir_agencias.py`

O banco original tem 10 agências. Este script cria mais 90 para simular o crescimento do banco entre 2023 e 2026.

Cada agência tem endereço, cidade, estado, coordenadas GPS e meta comercial mensal.

```bash
python scripts/expandir_agencias.py
# Resultado: data/sintetico/agencias_expandidas.csv (100 agências)
```

**Precisa de:** nada — roda independente.

---

### `expandir_colaboradores.py`

O banco original tem 100 funcionários. Este script cria mais 1.100 com cargos reais (de Diretoria até Operacional), departamentos, salários e em qual agência trabalham.

```bash
python scripts/expandir_colaboradores.py
# Resultado: data/sintetico/colaboradores_expandidos.csv (1.200 funcionários)
```

**Precisa de:** `agencias_expandidas.csv` (rodar o script anterior antes).

---

### `gerar_dados_sinteticos.py`

Este é o maior script. Ele expande o banco de ~1.000 clientes para 50.000, preservando as mesmas proporções e comportamentos dos dados reais.

```bash
# Tudo de uma vez (recomendado — order automática)
python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42

# Ou etapa por etapa:
python scripts/gerar_dados_sinteticos.py --etapa clientes      # gera 50.000 clientes
python scripts/gerar_dados_sinteticos.py --etapa contas        # ~70.000 contas
python scripts/gerar_dados_sinteticos.py --etapa propostas     # ~56.000 propostas

# Depois das etapas acima, essas podem rodar em qualquer ordem:
python scripts/gerar_dados_sinteticos.py --etapa investimentos
python scripts/gerar_dados_sinteticos.py --etapa seguros
python scripts/gerar_dados_sinteticos.py --etapa fraudes
python scripts/gerar_dados_sinteticos.py --etapa cartoes
python scripts/gerar_dados_sinteticos.py --etapa inadimplencia

# Por último (arquivo mais pesado — ~3 milhões de linhas):
python scripts/gerar_dados_sinteticos.py --etapa transacoes
```

O `--seed 42` garante que você sempre vai gerar os mesmos números. Se trocar o número, vai gerar dados diferentes.

---

### `projetar_series_historicas.py`

Os dados do IBGE e do Banco Central vão até 2024 ou 2025. Este script projeta os valores até 2026 usando crescimento histórico médio.

```bash
python scripts/projetar_series_historicas.py
# Resultado: 5 arquivos em external_data/projecoes/
```

| Arquivo gerado | O que contém |
|---|---|
| `ipca_projetado.csv` | Inflação real (2010–2025) + projetada (2026) |
| `selic_projetada.csv` | Taxa de juros real + projetada |
| `cdi_projetado.csv` | Taxa CDI real + projetada |
| `populacao_projetada.csv` | População por cidade real + projetada |
| `pib_projetado.csv` | PIB por cidade real + projetado |

**Precisa de:** `download_datasets.py` ter rodado antes.

---

## Grupo 2 — Pipeline ETL

### `entrypoint.py`

Este é o script "faz tudo". Ele chama os outros na ordem certa: configura o banco → carrega os dados brutos → limpa os dados → cria o modelo final → verifica as respostas.

```bash
# Pipeline completo (recomendado na primeira vez)
python scripts/entrypoint.py

# Pular a configuração inicial (banco já foi configurado antes)
python scripts/entrypoint.py --skip-setup

# Rodar só uma camada
python scripts/entrypoint.py --only gold
```

**Precisa de:** Docker rodando (`docker compose up -d`) e dados gerados.

---

### `carga_bronze.py`

Pega todos os arquivos CSV e carrega no banco PostgreSQL. É como importar uma planilha para o banco, mas para 35 arquivos de uma vez.

```bash
# Carregar tudo
python scripts/carga_bronze.py

# Carregar só um grupo
python scripts/carga_bronze.py --grupo banvic      # dados originais do banco
python scripts/carga_bronze.py --grupo sintetico   # dados gerados
python scripts/carga_bronze.py --grupo externo     # dados públicos (BCB, IBGE...)
```

**Precisa de:** PostgreSQL rodando e o schema Bronze criado (`sql/01_bronze/ddl_bronze.sql`).

---

## Grupo 3 — Validação

### `validar_gabarito.py`

Calcula as 8 respostas (KPIs) diretamente dos arquivos CSV originais, sem precisar do banco. É a fonte da verdade — os números que todos os 9 projetos precisam bater.

```bash
python scripts/validar_gabarito.py
python scripts/validar_gabarito.py --kpi 1   # só a KPI 1
```

Gera: `docs/gabarito/gabarito.json` e `docs/gabarito/gabarito_resumo.txt`

---

### `gerar_gabarito_gold.py`

Depois que o Projeto 1 (SQL Puro) estiver completo, use este script para gerar um novo gabarito a partir do banco PostgreSQL. Este gabarito inclui também os dados sintéticos.

```bash
python scripts/gerar_gabarito_gold.py
```

**Precisa de:** Projeto 1 completo (Gold layer populado no PostgreSQL).

---

### `validar_gabarito_pg.py`

Este é o "juiz" dos projetos. Ele consulta o banco, calcula as 8 KPIs e compara com o gabarito. Se todos batem: **APROVADO**.

```bash
python scripts/validar_gabarito_pg.py

# Com tolerância de 1% de diferença
python scripts/validar_gabarito_pg.py --tolerancia 0.01

# Validar só uma KPI
python scripts/validar_gabarito_pg.py --kpi 1
```

---

## Ordem Completa (do zero ao fim)

```bash
# PREPARAÇÃO — rodar uma vez
python scripts/download_datasets.py
python scripts/expandir_agencias.py
python scripts/expandir_colaboradores.py
python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42
python scripts/projetar_series_historicas.py
python scripts/validar_gabarito.py           # gera o gabarito dos dados originais

# PIPELINE — subir o banco e carregar tudo
docker compose up -d
python scripts/entrypoint.py

# VALIDAÇÃO — verificar se as respostas estão certas
python scripts/validar_gabarito_pg.py
```

---

## Dependências Python

```bash
pip install -r requirements.txt
# Os principais pacotes:
# psycopg2-binary  — conexão com PostgreSQL
# pandas           — manipulação de dados
# faker            — geração de dados fictícios realistas
# numpy            — cálculos numéricos
# python-dotenv    — ler o arquivo .env
# requests         — fazer chamadas às APIs (BCB, IBGE)
```
