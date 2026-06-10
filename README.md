# BanVic 360 — Portfolio de Engenharia de Dados

Simulacao de um banco nacional brasileiro (2023-2026) resolvida com **9 stacks diferentes**, sempre chegando nos mesmos **8 KPIs validados por um gabarito imutavel**.

> **Tese:** Um problema bancario real, 9 abordagens tecnicas, uma unica resposta correta.

---

## Os 9 Projetos

| # | Stack | Principal habilidade demonstrada | Pergunta respondida |
|---|---|---|---|
| 1 | SQL + PostgreSQL | Modelagem dimensional e SQL avancado | Como construir um DW com poucas dependencias? |
| 2 | Python + PostgreSQL | ETL programatico e tratamento de erros | Quando as regras exigem mais controle por codigo? |
| 3 | Apache Hop | ETL visual e operacao low-code | Quando uma interface visual facilita a operacao? |
| 4 | Docker | Reproducibilidade e infraestrutura local | Como eliminar o "funciona so na minha maquina"? |
| 5 | Airflow | Orquestracao, dependencias e backfill | Como operar pipelines recorrentes com seguranca? |
| 6 | dbt | ELT, testes, documentacao e lineage | Como organizar transformacao SQL em equipe? |
| 7 | Databricks | Processamento distribuido e Lakehouse | Como lidar com volumes maiores e historico ACID? |
| 8 | n8n | Integracoes, APIs e automacao low-code | Quando automatizar fluxos orientados a eventos? |
| 9 | Fabric + Power BI | Plataforma integrada e entrega ao negocio | Como entregar dados ate o dashboard executivo? |

Cada projeto termina com: carga dos mesmos dados, 8 KPIs corretos, comparacao automatica com o gabarito e uma conclusao sobre quando usar aquela solucao.

---

## Estrutura de Pastas

```
banvic/
|-- data/
|   |-- banvic/          # CSVs originais (998 clientes, 72k transacoes) - IMUTAVEL
|   `-- sintetico/       # Dados sinteticos gerados (50k clientes, 3M+ transacoes)
|-- external_data/       # 14 datasets publicos (BCB, IBGE, Open-Meteo)
|-- sql/
|   |-- 00_setup/        # Schemas e extensoes PostgreSQL
|   |-- 01_bronze/       # DDL e carga bruta (COPY)
|   |-- 02_silver/       # Transformacoes e Data Quality
|   `-- 03_gold/         # Star schema dimensional (9 dims + 9 fatos + 8 KPI views)
|-- scripts/             # Scripts Python utilitarios
|-- projetos/            # Os 9 projetos (cada um em sua pasta)
|-- docs/                # Arquitetura, gabarito, roadmap
|-- docker-compose.yml
|-- requirements.txt
`-- .env.example
```

---

## Pre-requisitos

- Python 3.10+
- Docker e Docker Compose (recomendado)
- PostgreSQL 15+ (ou use o docker-compose abaixo)

---

## Inicio Rapido (Docker)

```bash
# 1. Copiar variaveis de ambiente
cp .env.example .env

# 2. Subir banco de dados
docker compose up -d

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Gerar dados sinteticos (primeira vez)
python scripts/gerar_dados_sinteticos.py --etapa tudo --seed 42

# 5. Carregar e validar (setup -> bronze -> silver -> gold -> validacao)
python scripts/entrypoint.py
```

Apos o passo 5:
- PostgreSQL disponivel em `localhost:5432`
- pgAdmin disponivel em `http://localhost:5050` (admin@banvic.local / admin)
- 8 KPIs validados contra o gabarito

---

## Os 8 KPIs — Gabarito Imutavel

Todo projeto deve reproduzir exatamente estes resultados:

| # | KPI | Logica |
|---|---|---|
| 1 | Saldo sob gestao por agencia | `SUM(saldo_total) GROUP BY agencia` |
| 2 | Volume de transacoes por mes e tipo | `SUM(valor), COUNT GROUP BY mes, nome_transacao` |
| 3 | Mix de transacoes (%) | `% de cada tipo sobre total do mes` |
| 4 | Conversao de propostas | `COUNT por status_proposta + valor medio` |
| 5 | Ranking de agencias | `Saldo + volume ordenado DESC` |
| 6 | Carteira por colaborador | `Contas geridas, saldo, propostas aprovadas` |
| 7 | Segmentacao por faixa etaria | `Faixas etarias vs saldo medio` |
| 8 | Correcao IPCA | `valor_real = valor_nominal x indice_base / indice_mes` |

Gabarito calculado em: `docs/gabarito/gabarito.json`

---

## Dados

| Fonte | Registros | Descricao |
|---|---|---|
| `data/banvic/` | ~72k transacoes | Dados originais do banco (imutaveis) |
| `data/sintetico/` | 2.6M+ transacoes | Expansao sintetica (50k clientes) |
| `external_data/` | 14 datasets | BCB (Selic, CDI, IPCA), IBGE, Open-Meteo |

---

## Documentacao

- [Arquitetura](docs/arquitetura-lakehouse-banvic.md)
- [Roadmap](docs/roadmap-portfolio-banvic.md)
- [Gabarito dos KPIs](docs/gabarito/gabarito_resumo.txt)
- [Data Quality Framework](sql/02_silver/data_quality_framework.sql)

---

## Quando Usar Cada Stack

A conclusao do portfolio nao declara uma vencedora absoluta. A resposta profissional e contextual:

| Cenario | Stack recomendada |
|---|---|
| Dados pequenos, equipe SQL-first | PostgreSQL puro |
| Regras de negocio complexas | Python + PostgreSQL |
| Equipe low-code / BI | Apache Hop |
| Reproducibilidade garantida | Docker |
| Pipelines em producao com retry | Airflow |
| Transformacao governada em equipe | dbt |
| Dados > 100GB ou streaming | Databricks |
| Integracoes rapidas com APIs | n8n |
| Organizacao Microsoft-first | Fabric + Power BI |
