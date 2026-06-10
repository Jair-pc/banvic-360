# Projeto 6 — dbt (Modern Data Stack)

Pipeline ELT do BanVic 360 implementado com **dbt Core**, rodando sobre o PostgreSQL
que já tem o Bronze carregado. A transformação acontece inteiramente dentro do banco —
dbt compila os models em SQL e executa na ordem certa, com testes embutidos.

**Pergunta central:** _Como organizar transformação SQL em equipe — com testes, documentação e lineage automáticos?_

---

## Stack técnica

| Conceito dbt | Arquivo | Por que usei |
|---|---|---|
| `{{ source() }}` | Silver models | Referencia Bronze com rastreabilidade — dbt sabe de onde vêm os dados |
| `{{ ref() }}` | Gold models | Dependências declaradas — dbt resolve a ordem de execução automaticamente |
| `{{ config(materialized='table') }}` | Silver + Gold dims/fatos | Recria as tabelas a cada run |
| `{{ config(materialized='view') }}` | KPI marts | Sempre calcula em cima dos fatos mais recentes, sem armazenamento extra |
| `{{ faixa_etaria(...) }}` macro | Silver clientes | Lógica reutilizável em qualquer model |
| `generate_schema_name` macro | macros/ | Controla em qual schema cada model é criado (`silver`, `gold`) |
| `schema.yml` tests | silver/, gold/ | `not_null`, `unique`, `accepted_values`, `relationships` embutidos |
| Singular test | `tests/assert_kpi1_validacao.sql` | Valida o total do KPI1 contra o gabarito (R$ 26.509.620,12) |
| Lineage automático | `dbt docs generate` | Grafo de dependências visível sem documentação manual |

---

## Estrutura dos arquivos

```
06-dbt/
├── banvic_dbt/
│   ├── dbt_project.yml                     Config do projeto
│   ├── profiles.yml                        Conexao PostgreSQL via env vars
│   ├── macros/
│   │   ├── generate_schema_name.sql        Garante silver/gold como schemas exatos
│   │   └── faixa_etaria.sql                Macro reutilizavel de faixa etaria
│   ├── models/
│   │   ├── sources.yml                     Declaracao das tabelas Bronze
│   │   ├── silver/
│   │   │   ├── schema.yml                  Testes: not_null, unique, accepted_values
│   │   │   ├── clientes.sql                Bronze -> Silver (real + sintetico, dedup)
│   │   │   ├── contas.sql
│   │   │   ├── transacoes.sql              Deriva canal do nome_transacao
│   │   │   ├── agencias.sql
│   │   │   ├── colaboradores.sql
│   │   │   └── propostas.sql
│   │   └── gold/
│   │       ├── dims/
│   │       │   ├── schema.yml              Testes: unique, relationships
│   │       │   ├── dim_tempo.sql           Calendar 2010-2026 + Selic/CDI/PTAX/IPCA
│   │       │   ├── dim_cliente.sql
│   │       │   ├── dim_agencia.sql
│   │       │   ├── dim_colaborador.sql     Referencia dim_agencia via ref()
│   │       │   └── dim_canal.sql
│   │       ├── fatos/
│   │       │   ├── schema.yml              Testes: relationships com dims
│   │       │   ├── fato_transacoes.sql
│   │       │   ├── fato_contas.sql
│   │       │   └── fato_propostas_credito.sql
│   │       └── marts/
│   │           ├── kpi1_saldo_agencia.sql  View: saldo por agencia (KPI 1 + 5)
│   │           └── kpi4_conversao_propostas.sql
│   └── tests/
│       └── assert_kpi1_validacao.sql       Valida total saldo vs gabarito
├── docker-compose.yml                      dbt Core 1.8 via Docker
├── run.bat                                 Windows
└── run.sh                                  Linux/Mac
```

---

## Como executar

### Pre-requisitos

Bronze carregado no PostgreSQL:
```bash
# Na raiz do projeto
docker compose up -d
python scripts/carga_bronze.py
```

### Pipeline completo

**Windows:**
```bat
cd projetos\06-dbt
run.bat
```

**Linux/Mac:**
```bash
cd projetos/06-dbt
chmod +x run.sh && ./run.sh
```

**Ou por etapa:**
```bash
# Transformar (Bronze -> Silver -> Gold)
docker compose run --rm dbt run --profiles-dir /banvic_dbt

# Rodar testes
docker compose run --rm dbt test --profiles-dir /banvic_dbt

# Gerar e visualizar documentacao
docker compose run --rm dbt docs generate --profiles-dir /banvic_dbt
docker compose run --rm -p 8081:8080 dbt docs serve
# Acesse http://localhost:8081
```

### dbt local (sem Docker)

```bash
pip install dbt-postgres==1.8.0
cd projetos/06-dbt/banvic_dbt

# Definir variáveis de ambiente
export BANVIC_PG_HOST=localhost
export BANVIC_PG_USER=banvic_user
export BANVIC_PG_PASSWORD=banvic_pass
export BANVIC_PG_DATABASE=banvic

dbt run --profiles-dir .
dbt test --profiles-dir .
```

---

## Lineage do projeto

```
bronze.clientes ──────────────────────────┐
bronze.clientes_sinteticos ───────────────┤
                                          ▼
                                   silver.clientes ───────────────────────────┐
                                                                               ▼
bronze.contas ─────────────────── silver.contas ───────────────┐     gold.dim_cliente
                                                               ▼
bronze.transacoes ─────────────── silver.transacoes ────────── gold.dim_canal
                                                               │
bronze.agencias ───────────────── silver.agencias ──────────── gold.dim_agencia ──┐
bronze.agencias_expandidas ──────────────────────────────────────────────────────┘
                                                                                   │
bronze.colaboradores ───────────  silver.colaboradores ─── gold.dim_colaborador   │
bronze.colaboradores_expandidos ──────────────────────────────────────────────    │
                                                                                   │
bronze.selic / cdi / ptax / ipca / feriados ─────────── gold.dim_tempo            │
                                                                                   │
                                           ┌──────────────────────────────────────┘
                                           ▼
                                    gold.fato_transacoes ── gold.kpi1_saldo_agencia
                                    gold.fato_contas      ── gold.kpi4_conversao_propostas
bronze.propostas_credito ─────── gold.fato_propostas_credito
```

---

## Testes incluídos

| Tipo | Exemplo | O que valida |
|---|---|---|
| `not_null` | `silver.clientes.cod_cliente` | Chaves nunca nulas |
| `unique` | `gold.dim_tempo.sk_tempo` | Sem duplicatas |
| `accepted_values` | `silver.transacoes.canal` | Canal só aceita os 9 valores mapeados |
| `relationships` | `fato_transacoes.sk_tempo → dim_tempo` | FK referential integrity |
| Singular test | `tests/assert_kpi1_validacao.sql` | Saldo total bate com o gabarito |

---

## Por que dbt é diferente dos projetos anteriores

| Capacidade | SQL Puro | Python | Airflow | dbt |
|---|---|---|---|---|
| Ordem de execução | Manual | Manual | DAG explícita | **Automática via `ref()`** |
| Testes de dados | Nenhum | Unittest | Nenhum | **Embutido no YAML** |
| Documentação | Nenhuma | Nenhuma | Nenhuma | **`dbt docs` automático** |
| Lineage visual | Nenhum | Nenhum | Gráfico de tasks | **Grafo completo fonte→tabela** |
| Versionamento de lógica | Scripts SQL | Arquivos .py | DAGs | **Model SQL com histórico** |
| Abstração de lógica | Nenhuma | Funções Python | Operators | **Macros Jinja** |
| Colaboração em equipe | Difícil | Médio | Médio | **Fácil — SQL padrão** |

O grande ganho do dbt não é performance — é a capacidade de um time de dados
trabalhar na mesma base de transformação sem pisar no código de outro.
Cada model é um arquivo SQL versionado, testável, documentado e com rastreabilidade
automática. Em Projetos 1-5, qualquer mudança no pipeline exige entender o código todo.
Em dbt, cada model é independente.

---

## Quando usar dbt

| Cenário | dbt é ideal? |
|---|---|
| Time de dados que escreve SQL | **Sim** — curva de aprendizado baixa |
| Warehouse já consolidado (Snowflake, BQ, Redshift, PG) | **Sim** — funciona com qualquer SQL engine |
| Necessidade de testes e documentação automáticos | **Sim** — é o ponto forte |
| Transformações com lógica de negócio em Python/ML | **Não** — use Python puro ou Spark |
| Ingestão de dados (Bronze loading) | **Não** — dbt não move dados, só transforma |
| Orquestração com retries e agendamento | **Com integração** — use dbt + Airflow/Prefect |

dbt não é um pipeline completo — é a camada de transformação de um pipeline.
O padrão da indústria é usar dbt para as transformações dentro do warehouse e
Airflow (ou similar) para orquestrar o pipeline completo: ingestão → dbt run → alertas.
