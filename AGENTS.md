# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

> **Para toda nova sessão:** leia este arquivo primeiro. É a fonte de verdade do projeto.
> Última atualização: 2026-06-10 (sessão 5 — REVISÃO DOCUMENTAL)

---

## PROJETO

**BanVic (Banco Vitória)** — portfólio profissional de Engenharia de Dados que simula um banco nacional brasileiro em crescimento (2023–2026).

Tese central: **"Um problema bancário real, resolvido em 9 stacks diferentes — chegando sempre nas mesmas respostas validadas por um gabarito."**

Targets de carreira: Analista de Dados, BI, Analytics Engineer, Eng. de Dados Jr.

---

## COMANDOS

### Dependências Python

```bash
pip install faker numpy requests
```

### Dados externos (re-download)

```bash
# Re-baixar todos os 14 datasets externos
python scripts/download_datasets.py

# Dataset específico
python scripts/download_datasets.py --dataset ipca
python scripts/download_datasets.py --dataset clima   # aumentar sleep p/ 1s para cidades faltantes
```

### Expansão de estrutura (rodar uma vez, nessa ordem)

```bash
# 1. Gerar 100 agências (sem dependências)
python scripts/expandir_agencias.py

# 2. Gerar 1.200 colaboradores (requer agencias_expandidas.csv)
python scripts/expandir_colaboradores.py
```

### Geração de dados sintéticos (ordem obrigatória)

```bash
# Etapas que devem rodar em sequência (cada uma depende da anterior):
python scripts/gerar_dados_sinteticos.py --etapa clientes      # 50.000 clientes
python scripts/gerar_dados_sinteticos.py --etapa contas        # ~70.000 contas
python scripts/gerar_dados_sinteticos.py --etapa propostas     # ~56.000 propostas

# Após contas e propostas, essas etapas são independentes entre si:
python scripts/gerar_dados_sinteticos.py --etapa investimentos
python scripts/gerar_dados_sinteticos.py --etapa seguros
python scripts/gerar_dados_sinteticos.py --etapa fraudes
python scripts/gerar_dados_sinteticos.py --etapa cartoes
python scripts/gerar_dados_sinteticos.py --etapa inadimplencia  # requer propostas

# Mais pesada (~3M linhas, rodar por último):
python scripts/gerar_dados_sinteticos.py --etapa transacoes

# Ou tudo de uma vez (respeitando a ordem automaticamente):
python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42
```

### Observações de ambiente (Windows)

- **Encoding:** todos os `print()` devem usar apenas ASCII — o console Windows (cp1252) não suporta `✓`, `→`, `→`. Usar `OK` e `->` nos scripts.
- **Python:** 3.14 em `C:\Python314\`
- **Diretório raiz:** `c:\Projeto\ETL e ELT\`

---

## ESTADO ATUAL (atualizar a cada sessão)

### ✅ Concluído

**Sessões 1–3:**
- Diagnóstico completo dos dados internos
- 14 datasets externos coletados (`external_data/`)
- DDL projetado do modelo dimensional Gold (9 dims + 9 fatos + 8 KPI views): `sql/03_gold/ddl_modelo_dimensional.sql`
- Framework DQ (regras, funções CPF/CEP, scorecard): `sql/02_silver/data_quality_framework.sql`
- Documentação: arquitetura, catálogo, roadmap, data dictionary

**Sessão 4:**
- [x] `scripts/expandir_agencias.py` — 100 agências, distribuição nacional, timeline 2024/2025/2026
- [x] `data/sintetico/agencias_expandidas.csv` — 100 agências (10 originais + 90 novas)
- [x] `scripts/expandir_colaboradores.py` — 1.200 colaboradores com hierarquia completa
- [x] `data/sintetico/colaboradores_expandidos.csv` — 1.200 colaboradores
- [x] `scripts/gerar_dados_sinteticos.py` — script completo com 9 etapas
- [x] `data/sintetico/clientes_sinteticos.csv` — 50.000 clientes
- [x] `data/sintetico/contas_sinteticas.csv` — 70.121 contas
- [x] `data/sintetico/propostas_sinteticas.csv` — 56.635 propostas
- [x] `data/sintetico/investimentos.csv` — 16.008 posições (patrimônio ativo: R$273M)
- [x] `data/sintetico/seguros.csv` — 17.769 apólices (prêmio mensal: R$3,7M)
- [x] `data/sintetico/cartoes.csv` — 537.694 faturas
- [x] `data/sintetico/inadimplencia.csv` — 468 contratos (carteira: R$17,2M)
- [x] `data/sintetico/fraudes.csv` — 1.400 ocorrências (460 confirmadas)
- [x] `data/sintetico/transacoes_sinteticas.csv` — 2.642.400 transações (2023–2026)

**Sessão 5 (atual):**
- [x] Documentação sincronizada com o estado real dos datasets e dados sintéticos
- [x] Grão oficial de `fato_contas` corrigido nos documentos: 1 linha por conta (snapshot corrente)
- [x] Metas antigas substituídas pelos volumes efetivamente gerados
- [x] Roadmap atualizado: Fundação concluída; próximo marco é o Projeto 1

### ⚠️ Observações sobre dados externos

| Dataset | Arquivo | Status |
|---|---|---|
| Renda municipal | `geografia/renda_municipal.csv` | ⚠️ estimativa (PIB/12) — IBGE tabela 9605 retornou 500 |
| Escolaridade | `geografia/escolaridade_municipal.csv` | ⚠️ placeholder — IBGE tabela 9612 retornou 500 |
| Clima histórico | `clima/clima_historico.csv` | ⚠️ 91/99 cidades — 8 falharam por rate limit 429 |
| Desemprego | `macroeconomia/desemprego.csv` | Série correta: **BCB SGS-24369** (taxa %). A 28763 retorna número absoluto |

### ✅ PRÉ-PROJETO COMPLETO — pronto para iniciar os 9 projetos

Todas as 18 fases de preparação concluídas. **Próximo: Projeto 1 — SQL Puro (PostgreSQL).**

Sequência para carregar no PostgreSQL:
1. `sql/00_setup/00_schemas_extensoes.sql`
2. `sql/01_bronze/ddl_bronze.sql`
3. `sql/01_bronze/carga_bronze.sql`
4. `sql/02_silver/data_quality_framework.sql`
5. `sql/02_silver/ddl_silver_transforms.sql`
6. `sql/03_gold/ddl_modelo_dimensional.sql`
7. Verificar com `python scripts/validar_gabarito.py`

---

## ARQUITETURA — LAKEHOUSE BANVIC

### Camadas de dados

```
data/banvic/          ← IMUTÁVEL: CSVs originais do banco (998 clientes, 72k transações)
data/sintetico/       ← Gerado: expansão sintética (50k clientes, 3M+ transações)
external_data/        ← Coletado: 14 datasets públicos (BCB, IBGE, Open-Meteo)

BRONZE (PostgreSQL)   ← Ingestão bruta via COPY, sem transformação
SILVER (PostgreSQL)   ← Limpo, tipado, padronizado; DQ aplicado
GOLD (PostgreSQL)     ← Star schema dimensional para analytics
```

### Modelo dimensional Gold (star schema)

**9 Dimensões:** `dim_tempo` (com Selic/CDI/PTAX/IPCA por dia), `dim_cliente` (SCD Tipo 2), `dim_agencia`, `dim_colaborador`, `dim_municipio` (com PIB/população IBGE), `dim_produto` (28 produtos pré-inseridos), `dim_canal`, `dim_score_credito`, `dim_clima`

**9 Fatos:** `fato_transacoes`, `fato_contas` (snapshot corrente: 1 linha por conta), `fato_propostas_credito`, `fato_investimentos`, `fato_cartoes` (faturas), `fato_seguros` (apólices), `fato_inadimplencia`, `fato_receitas`, `fato_fraudes`

DDL projetado: `sql/03_gold/ddl_modelo_dimensional.sql`. A execução ponta a ponta e a validação das views Gold contra o gabarito pertencem ao Projeto 1.

### Relacionamentos originais (data/banvic/)

```
clientes  ──▶ contas       (cod_cliente)
contas    ──▶ transacoes   (num_conta)
contas    ──▶ agencias     (cod_agencia)
contas    ──▶ colaboradores (cod_colaborador)
propostas ──▶ clientes     (cod_cliente)
propostas ──▶ colaboradores (cod_colaborador)
```

---

## OS 8 KPIs — GABARITO (IMUTÁVEIS)

Todo projeto (SQL, Python, dbt, Databricks etc.) deve reproduzir exatamente estes resultados:

| # | KPI | Lógica |
|---|---|---|
| 1 | Saldo sob gestão por agência | `SUM(saldo_total) GROUP BY agencia` |
| 2 | Volume de transações por mês e tipo | `SUM(valor), COUNT GROUP BY mes, nome_transacao` |
| 3 | Mix de transações (%) | `% de cada tipo sobre total do mês` |
| 4 | Conversão de propostas | `COUNT por status_proposta + valor médio` |
| 5 | Ranking de agências | `Saldo + volume ordenado DESC` |
| 6 | Carteira por colaborador | `contas geridas, saldo, propostas aprovadas` |
| 7 | Segmentação por faixa etária | `faixas etárias vs saldo médio` |
| 8 | Correção IPCA | `valor_real = valor_nominal × indice_base / indice_mes` |

**Regras fixadas:**
- `fato_contas` grain = 1 linha por conta (snapshot corrente, não histórico)
- KPI #8: mês-base = último mês disponível no `ipca.csv`
- IPCA: base Jan/2010 = 3040.22 (índice acumulado IBGE)

---

## OS 9 PROJETOS — LINHA DO TEMPO

| # | Stack | Status |
|---|---|---|
| 0 | Fundação / Gabarito (SQL + Python) | ⏳ próximo |
| 1 | SQL Puro (PostgreSQL) | ⏳ |
| 2 | Python + PostgreSQL | ⏳ |
| 3 | Apache Hop | ⏳ |
| 4 | Docker + Ambiente | ⏳ |
| 5 | Airflow + Python | ⏳ |
| 6 | Modern Data Stack (dbt) | ⏳ |
| 7 | Databricks Lakehouse | ⏳ |
| 8 | n8n | ⏳ |
| 9 | Microsoft Fabric + Power BI | ⏳ |

---

## DADOS SINTÉTICOS — ESCALA E DISTRIBUIÇÕES

| Arquivo | Registros | Notas |
|---|---|---|
| `clientes_sinteticos.csv` | 50.000 | Renda lognormal (mediana ~R$3.5k), score correlacionado com renda |
| `contas_sinteticas.csv` | ~70.000 | 1-3 contas por cliente, 65% têm 1 conta |
| `transacoes_sinteticas.csv` | 2.642.400 | Sazonalidade mensal preservada; dez=140%, fev=80% |
| `propostas_sinteticas.csv` | ~56.000 | Taxa de aprovação varia por faixa de score |
| `investimentos.csv` | ~16.000 | Prob de investir: maior com renda e score altos |
| `cartoes.csv` | ~537.000 | Faturas mensais; 75% pagam total |
| `seguros.csv` | ~17.000 | 25% são cross-sell |
| `inadimplencia.csv` | ~468 | Bucket 0-30/31-60/61-90/90+; NPL calculável |
| `fraudes.csv` | ~1.400 | 65% tentativas, 35% confirmadas |
| `agencias_expandidas.csv` | 100 | 10→20(2024)→50(2025)→100(2026) |
| `colaboradores_expandidos.csv` | 1.200 | 4 níveis hierárquicos; cargo + salário + agência |

**Seed padrão:** 42 (reprodutível). Trocar com `--seed N`.

---

## CONVENÇÕES DE NOMENCLATURA

| Contexto | Padrão | Exemplo |
|---|---|---|
| Tabelas Gold | `dim_` ou `fato_` | `dim_cliente`, `fato_transacoes` |
| Tabelas Silver | sufixo `_clean` | `clientes_clean` |
| Tabelas Bronze | prefixo `bronze_` | `bronze_transacoes` |
| Chaves surrogate | prefixo `sk_` | `sk_cliente` |
| Chaves naturais | `cod_` ou `num_` | `cod_cliente`, `num_conta` |
| Campos de data | prefixo `data_` | `data_transacao`, `data_abertura` |
| Flags booleanos | `eh_` ou `flag_` | `eh_feriado`, `flag_ativo` |
| Campos de valor | prefixo `valor_` | `valor_transacao`, `valor_proposta` |

---

## DECISÕES TÉCNICAS FIXADAS

| Decisão | Escolha |
|---|---|
| Encoding todos os arquivos | UTF-8 sem BOM |
| Formato de datas | `YYYY-MM-DD` (ISO 8601) |
| Separador decimal | `.` (ponto) |
| Modelo DW | Star schema (compatível com todos os 9 projetos) |
| Grain `fato_contas` | 1 linha/conta (snapshot corrente) |
| Console Windows | Evitar caracteres non-ASCII em `print()` |

---

## ARQUIVOS-CHAVE

| Arquivo | Propósito |
|---|---|
| `sql/03_gold/ddl_modelo_dimensional.sql` | DDL projetado: 9 dims + 9 fatos + 8 KPI views |
| `sql/02_silver/data_quality_framework.sql` | Regras DQ + função `valida_cpf()` + scorecard |
| `scripts/download_datasets.py` | CLI de re-download dos 14 datasets externos |
| `scripts/gerar_dados_sinteticos.py` | Gerador completo com 9 etapas (50k clientes, 3M+ tx) |
| `scripts/expandir_agencias.py` | 100 agências com lat/lon e timeline histórica |
| `scripts/expandir_colaboradores.py` | 1.200 colaboradores com hierarquia e salários |
| `scripts/projetar_series_historicas.py` | Projeções IPCA/Selic/CDI/PIB/Pop até 2026 |
| `scripts/validar_gabarito.py` | Calcula 8 KPIs dos dados reais → `docs/gabarito/` |
| `sql/00_setup/00_schemas_extensoes.sql` | Cria schemas + extensões PostgreSQL |
| `sql/01_bronze/ddl_bronze.sql` | DDL de todas as tabelas Bronze (TEXT) |
| `sql/01_bronze/carga_bronze.sql` | COPY commands para carregar todos os CSVs |
| `sql/02_silver/ddl_silver_transforms.sql` | Transforms Bronze→Silver (tipagem + limpeza) |
| `docs/gabarito/gabarito.json` | KPIs calculados dos dados reais (gabarito definitivo) |
| `docs/gabarito/gabarito_resumo.txt` | Resumo legível dos 8 KPIs |
| `docs/plano-lakehouse-orquestracao-dashboard.md` | Fases 15-18: arquitetura, DAGs, Power BI, análises SQL |
| `docs/roadmap-portfolio-banvic.md` | Roadmap 12 meses detalhado |

---

## COMO CONTINUAR EM NOVA SESSÃO

1. Leia este AGENTS.md inteiro
2. Verifique **"Estado Atual"** e identifique o próximo passo
3. Confirme com o usuário antes de executar qualquer etapa nova
4. Ao terminar, **atualize "Estado Atual"** com o que foi concluído
