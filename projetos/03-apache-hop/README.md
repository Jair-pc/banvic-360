# Projeto 3 — Apache Hop

Pipeline ETL completo do BanVic 360 construído com **Apache Hop** via Docker.
A mesma arquitetura Bronze → Silver → Gold dos projetos anteriores, desta vez
com uma ferramenta visual low-code de ETL enterprise.

**Pergunta central:** _Quando uma ferramenta visual ETL faz mais sentido que scripts?_

---

## Stack técnica

| Conceito Hop | Arquivo | Por que usei |
|---|---|---|
| **ExecSQL transform** | `pipelines/*.hpl` | Executa SQL dentro de um pipeline visual |
| **RowGenerator** | `pipelines/*.hpl` | Gera linha trigger para acionar transforms sem input externo |
| **Workflow orquestração** | `workflows/00_banvic_pipeline.hwf` | Encadeia pipelines com fluxo sucesso/erro |
| **SQL action** | `workflows/00_banvic_pipeline.hwf` | DDL de limpeza antes do pipeline (idempotência) |
| **Metadata RDBMS** | `metadata/rdbms/banvic_pg.json` | Conexão parametrizada por variáveis de ambiente |
| **CDATA sections** | `*.hpl/*.hwf` | SQL multi-linha embutido em XML sem necessidade de escape |
| **Error handling visual** | workflow hops `evaluation=N` | Abort automático em qualquer falha de etapa |

---

## Estrutura dos arquivos

```
03-apache-hop/
├── hop/
│   ├── project-config.json             Config do projeto Hop
│   ├── metadata/
│   │   └── rdbms/
│   │       └── banvic_pg.json          Conexao PostgreSQL (vars de ambiente)
│   ├── pipelines/
│   │   ├── 01_silver.hpl               Bronze -> Silver (12 transforms)
│   │   ├── 02_gold_dims.hpl            Silver -> Gold Dims (8 transforms)
│   │   └── 03_gold_fatos.hpl           Silver -> Gold Fatos (5 transforms)
│   └── workflows/
│       └── 00_banvic_pipeline.hwf      Orchestracao completa + error handling
├── docker-compose.yml                  Hop 2.10 conectado a banvic_net
├── run.bat                             Execucao Windows
└── run.sh                              Execucao Linux/Mac
```

---

## Como executar

### Pré-requisitos

1. **Postgres rodando com Bronze carregado:**
   ```bash
   # Na raiz do projeto
   docker compose up -d
   python scripts/carga_bronze.py
   ```

2. **Docker** instalado e rodando.

### Pipeline completo via Docker

**Windows:**
```bat
cd projetos\03-apache-hop
run.bat
```

**Linux/Mac:**
```bash
cd projetos/03-apache-hop
chmod +x run.sh && ./run.sh
```

**Ou diretamente:**
```bash
cd projetos/03-apache-hop
docker compose up --abort-on-container-exit --exit-code-from hop
```

### Abrir no Hop GUI

1. Baixe Apache Hop em [hop.apache.org](https://hop.apache.org)
2. Abra o Hop GUI
3. **File → New Project** → aponte para `projetos/03-apache-hop/hop/`
4. Abra qualquer `.hpl` ou `.hwf` para visualizar o pipeline

### Validar KPIs

```bash
python scripts/validar_gabarito_pg.py
```

---

## Arquitetura do workflow

```
Start
  │
  ▼
Preparar ambiente (SQL Action)
  DROP Silver tables / TRUNCATE Gold tables
  │ sucesso           │ erro
  ▼                   ▼
01 Silver            ABORT
  │ sucesso           │ erro
  ▼                   ▼
02 Gold Dims         ABORT
  │ sucesso           │ erro
  ▼                   ▼
03 Gold Fatos        ABORT
  │ sucesso
  ▼
Sucesso
```

## Padrão dos pipelines

Todos os 3 pipelines seguem o mesmo padrão:

```
RowGenerator (1 linha) → ExecSQL 01 → ExecSQL 02 → ... → ExecSQL N → Dummy
```

- **RowGenerator**: gera 1 linha para acionar o fluxo (sem arquivo ou tabela de input)
- **ExecSQL**: executa uma instrução SQL por transform (`execute_each_row=N`, `single_statement=Y`)
- **Dummy**: descarta o output (o resultado útil está no banco)

---

## Resultado

```
Resultado: 7/7 KPIs corretos
APROVADO: todos os KPIs batem com o gabarito.
```

---

## SQL Puro vs Python vs Apache Hop

| Critério | Projeto 1 (SQL) | Projeto 2 (Python) | Projeto 3 (Hop) |
|---|---|---|---|
| Visual / Low-code | Não | Não | **Sim** |
| Debug interativo | Difícil | `df.head()` | **GUI + preview de dados** |
| Testabilidade unitária | Baixa | Alta | Média (cada transform isolável) |
| Auditoria / lineage | Manual | Manual | **Nativo** (metadata) |
| Reutilização de transforms | Difícil | Funções Python | **Shared transforms** |
| Curva de aprendizado SQL | Alta | Média | Baixa (arrastar e soltar) |
| Performance bruta | Melhor | Overhead pandas | Semelhante ao SQL |
| Scheduler nativo | Não | Não | **Sim** (Hop Server) |

## Quando usar Apache Hop

| Cenário | Hop é ideal? |
|---|---|
| Time sem background de programação | **Sim** — visual, low-code |
| Auditoria e compliance rigoroso | **Sim** — lineage nativo |
| Migrações entre bancos diferentes | **Sim** — abstração de banco |
| Pipelines com retry e error handling visual | **Sim** — tratamento nativo |
| Transformações complexas com ML | **Não** — use Python/Spark |
| Pipeline simples em time SQL-first | **Não** — SQL Puro ou dbt |

Apache Hop é a ferramenta certa quando o time não tem perfil de código mas precisa
de rastreabilidade, error handling e portabilidade entre ambientes. O investimento
está na curva de aprendizado da ferramenta, não em programação.
