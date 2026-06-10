# Projeto 3 — Apache Hop

## Objetivo

Implementar o pipeline ETL completo do BanVic 360 usando **Apache Hop** via Docker,
provando que o mesmo resultado pode ser alcançado com uma ferramenta visual low-code de ETL enterprise.

**Pergunta central:** _Quando uma ferramenta visual ETL supera scripts SQL e Python?_

---

## Diferenciais técnicos demonstrados

| Conceito Hop | Arquivo | Propósito |
|---|---|---|
| **ExecSQL transform** | `pipelines/*.hpl` | Executa SQL dentro de um pipeline visual |
| **RowGenerator** | `pipelines/*.hpl` | Gera linha trigger para acionar transforms sem input |
| **Workflow orquestração** | `workflows/00_banvic_pipeline.hwf` | Encadeia pipelines com fluxo sucesso/erro |
| **SQL action** | `workflows/00_banvic_pipeline.hwf` | Executa DDL de limpeza antes do pipeline |
| **Metadata RDBMS** | `metadata/rdbms/banvic_pg.json` | Conexão parametrizada por variáveis de ambiente |
| **hop:// protocol** | `${PROJECT_HOME}/...` | Referências relativas ao projeto Hop |
| **CDATA sections** | `*.hpl/*.hwf` | SQL multi-linha embutido em XML sem escape |
| **Error handling** | workflow hops `evaluation=N` | Abort automático em qualquer falha |

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

1. **Root docker-compose rodando** (PostgreSQL com Bronze carregado):
   ```bash
   # Na raiz do projeto
   docker compose up -d
   python scripts/carga_bronze.py
   # Gold DDL (se ainda nao executado):
   # psql < sql/03_gold/ddl_modelo_dimensional.sql
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

### Abrir no Hop GUI (visualização)

1. Baixe Apache Hop em [hop.apache.org](https://hop.apache.org)
2. Abra o Hop GUI
3. File → New Project → aponte para `projetos/03-apache-hop/hop/`
4. Abra qualquer `.hpl` ou `.hwf` para visualizar o pipeline

### Validar KPIs

```bash
# Na raiz do projeto
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

## Resultados esperados

```
Resultado: 7/7 KPIs corretos
APROVADO: todos os KPIs batem com o gabarito.
```

---

## Comparação SQL Puro vs Python vs Apache Hop

| Critério | Projeto 1 (SQL) | Projeto 2 (Python) | Projeto 3 (Hop) |
|---|---|---|---|
| Visual / Low-code | Não | Não | **Sim** |
| Debug interativo | Difícil | `df.head()` | **GUI + preview de dados** |
| Testabilidade unitária | Baixa | Alta | **Média** (cada transform isolável) |
| Auditoria / lineage | Manual | Manual | **Nativo** (metadata) |
| Reutilização de transforms | Difícil | Funções Python | **Shared transforms** |
| Curva de aprendizado SQL | Alta | Média | **Baixa** (arrastar e soltar) |
| Performance bruta | Melhor | Overhead pandas | Semelhante ao SQL |
| Scheduler nativo | Não | Não | **Sim** (Hop Server) |

### Quando usar Apache Hop

| Cenário | Hop é ideal? |
|---|---|
| Time sem background de programação | **Sim** — visual, low-code |
| Auditoria e compliance rigoroso | **Sim** — lineage nativo |
| Migrations entre bancos diferentes | **Sim** — abstração de banco |
| Pipelines críticos com retry automático | **Sim** — error handling visual |
| Transformações ultra-complexas (ML) | **Não** — use Python/Spark |
| Pipeline simples em time SQL-first | **Não** — SQL Puro ou dbt |

### Conclusão

Apache Hop democratiza o ETL para equipes sem background de programação,
oferecendo auditoria, error handling e portabilidade entre ambientes (local, remoto, cloud)
de forma visual. O custo é a curva de aprendizado da ferramenta e a dependência do JAR.
O Projeto 5 (Airflow) eleva este padrão com orquestração distribuída e monitoramento avançado.
