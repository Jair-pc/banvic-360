# Projeto 5 — Airflow + Python

Pipeline ETL do BanVic 360 orquestrado com **Apache Airflow**, rodando via Docker.
A mesma lógica Bronze → Silver → Gold dos projetos anteriores, agora com scheduling,
retry automático, paralelismo por entidade e validação como task final.

**Pergunta central:** _O que muda quando o pipeline precisa rodar todo dia, sozinho, e avisar quando falha?_

---

## Stack técnica

| Conceito Airflow | Arquivo | Por que usei |
|---|---|---|
| `ShortCircuitOperator` | `dags/banvic_pipeline.py` | Bloqueia toda a DAG se o Bronze ainda não foi carregado |
| `TaskGroup` | `dags/banvic_pipeline.py` | Agrupa Silver e Gold visualmente; mostra status por grupo na UI |
| `PythonOperator` paralelo | `dags/banvic_pipeline.py` | 7 entidades Silver rodam ao mesmo tempo |
| `PostgresHook` | `dags/banvic_pipeline.py` | Conexão gerenciada pelo Airflow — sem credencial no código |
| XCom | `dags/banvic_pipeline.py` | Passa resultado da validação para o log do scheduler |
| `retries=2, retry_delay=3min` | `default_args` | Resiliência contra falhas transientes de conexão |
| `catchup=False` | DAG config | Não reprocessa datas passadas ao ligar o scheduler |
| `max_active_runs=1` | DAG config | Garante que o pipeline não rode em paralelo consigo mesmo |
| `schedule_interval="0 6 * * *"` | DAG config | Execução diária às 06:00 |
| LocalExecutor | `docker-compose.yml` | Paralelismo local sem necessidade de Celery/Redis |

---

## Estrutura dos arquivos

```
05-airflow/
├── dags/
│   └── banvic_pipeline.py    DAG principal (Silver paralelo + Gold + validacao)
├── logs/                     Logs do Airflow (gerado em runtime)
├── docker-compose.yml        Airflow 2.9 com LocalExecutor + banco de metadados
├── run.bat                   Inicializacao Windows
└── run.sh                    Inicializacao Linux/Mac
```

---

## Arquitetura da DAG

```
check_bronze (ShortCircuitOperator)
    |
    v
preparar_ambiente
    |
    v
[TaskGroup: silver]  ← 7 tasks em paralelo
    clientes  contas  transacoes  agencias  colaboradores  propostas  externos
        |         |        |          |            |            |         |
        └─────────┴────────┴──────────┴────────────┴────────────┴─────────┘
                                      |
                                   indices
    |
    v
[TaskGroup: gold]
    dims
     |
    fatos
    |
    v
validar_kpis
```

O paralelismo das tasks Silver é gerenciado automaticamente pelo LocalExecutor.
Na prática, as 7 entidades criam tabelas independentes — nenhuma depende da outra
nesse estágio, então o Airflow as despacha todas ao mesmo tempo.

---

## Como executar

### Pré-requisitos

1. **BanVic Postgres rodando com Bronze carregado:**
   ```bash
   # Na raiz do projeto
   docker compose up -d
   python scripts/carga_bronze.py
   ```

2. **Docker** com `banvic_net` já criada (garantida pelo compose da raiz).

### Subir o Airflow

**Windows:**
```bat
cd projetos\05-airflow
run.bat
```

**Linux/Mac:**
```bash
cd projetos/05-airflow
chmod +x run.sh && ./run.sh
```

**Ou manualmente:**
```bash
cd projetos/05-airflow
docker compose up airflow-init          # primeira vez
docker compose up -d airflow-webserver airflow-scheduler
```

### Acessar a UI

`http://localhost:8080` — login: `admin` / `admin`

Na UI:
1. Localize a DAG `banvic_pipeline`
2. Ative o toggle (pausa por padrão)
3. Clique em **Trigger DAG** para rodar imediatamente

### Ver resultado da validação

Na UI: `banvic_pipeline → validar_kpis → Logs`

Ou via linha de comando:
```bash
docker logs banvic_airflow_scheduler | grep -i "validacao\|APROVAD\|falhou"
```

### Parar o Airflow

```bash
docker compose down
```

---

## Conexão com o BanVic Postgres

A conexão é declarada como variável de ambiente no compose:

```
AIRFLOW_CONN_BANVIC_PG=postgresql://banvic_user:banvic_pass@banvic_postgres:5432/banvic
```

O Airflow registra isso automaticamente como uma Connection com `conn_id="banvic_pg"`.
No DAG, `PostgresHook(postgres_conn_id="banvic_pg")` resolve a conexão sem
nenhuma credencial no código.

Em produção, essa variável viria de um Secret Manager (AWS, Vault, etc.) —
o código do DAG não muda, só a origem da variável de ambiente.

---

## O que o Airflow adiciona sobre scripts Python diretos

| Capacidade | Scripts Python | Airflow |
|---|---|---|
| Agendamento | Manual ou cron externo | **Nativo** — scheduler gerenciado |
| Retry automático | Implementar manualmente | **Nativo** — `retries` e `retry_delay` |
| Visualização de status | `print()` / log | **UI com gráfico de dependências** |
| Re-execução de task específica | Re-rodar o script todo | **Task individual via UI ou CLI** |
| Paralelismo | `threading` / `multiprocessing` | **Automático** pelo executor |
| Histórico de execuções | Arquivo de log | **Banco de metadados + UI** |
| Alertas em falha | Implementar manualmente | **`email_on_failure`, callbacks, Slack** |
| Backfill de datas passadas | Implementar manualmente | **`airflow dags backfill`** |

---

## Airflow em produção (VPS)

O setup deste projeto usa `LocalExecutor` — adequado para um servidor com
múltiplos CPUs onde todos os workers rodam no mesmo processo. Para escala maior:

| Executor | Quando usar |
|---|---|
| `LocalExecutor` | Single node, até ~50 tasks paralelas |
| `CeleryExecutor` | Multi-node, workers distribuídos |
| `KubernetesExecutor` | Tasks como pods K8s, escala dinâmica |

Para deploy em produção, o banco de metadados do Airflow (neste projeto: `airflow_meta`)
deve ser um PostgreSQL gerenciado (RDS, Cloud SQL) — não um container local.

---

## Quando usar Airflow

| Cenário | Airflow é ideal? |
|---|---|
| Pipeline recorrente com dependências entre tasks | **Sim** — é exatamente para isso |
| Necessidade de retry e alertas em falha | **Sim** — nativo |
| Time que precisa acompanhar status visualmente | **Sim** — UI clara |
| Backfill de dados históricos | **Sim** — `catchup=True` ou `backfill` CLI |
| Pipeline one-shot ou exploração | **Não** — overhead desnecessário |
| Equipe sem perfil DevOps para manter o Airflow | **Com cuidado** — Airflow tem custo operacional |
| Orquestração de notebooks ad-hoc | **Não** — use Papermill direto |

Airflow brilha quando o pipeline precisa ser confiável, auditável e operado por
mais de uma pessoa. O custo é a infraestrutura adicional (scheduler + banco de metadados)
e a curva de aprendizado para configuração inicial.
