# Roadmap Estratégico — Portfólio de Engenharia de Dados (BanVic)

> **Como ler este documento.** Ele foi escrito sob três chapéus: **Arquiteto de Dados Sênior**
> (arquitetura, trade-offs), **Analista de Dados Sênior** (perguntas de negócio, KPIs, BI) e
> **Tech Lead** (sequenciamento, riscos, narrativa de carreira). É um plano de 12 meses para sair
> de "sei usar ferramentas" para "resolvo problemas de negócio com a stack certa".
>
> **Estado em 2026-06-10:** pré-projeto e gabarito concluídos. O próximo marco é o Projeto 1,
> SQL Puro em PostgreSQL, incluindo execução reproduzível e validação automática da camada Gold.

**Premissas assumidas (ajuste se necessário):**
- **Base de negócio = BanVic** (banco fictício; os 8 CSVs em `data/` já são bancários).
- **Lineup = 9 projetos** na ordem do seu brief mais recente (substitui versões anteriores).
- **Diferencial central:** todos os 9 projetos resolvem o **mesmo problema** e chegam às **mesmas
  respostas** (validadas contra um gabarito), mudando só a stack. Isso é o que transforma
  "9 tutoriais" em "1 tese de portfólio".

---

## 1. Tese do portfólio e narrativa de carreira

**A tese (a frase que você repete em toda entrevista):**
> "Peguei um problema real de um banco e o resolvi de 9 formas diferentes — de SQL puro a Lakehouse
> — para mostrar que entendo não só *como* usar cada ferramenta, mas *quando* e *por quê* escolher
> cada uma."

**Por que isso é forte (visão de Tech Lead):** a maioria dos portfólios júnior é uma colcha de
retalhos de datasets aleatórios (Titanic, Iris, vendas fictícias). Usar **a mesma base** nos 9
projetos cria comparabilidade e mostra maturidade de arquiteto. O **risco** é parecer repetitivo —
neutralizamos isso com (a) um **capstone comparativo** (seção 9) e (b) um **ângulo único por
projeto** (cada um destaca uma capacidade diferente: modelagem, código, orquestração, governança…).

**Crítica honesta que você precisa ouvir:** recrutador júnior não lê 9 READMEs. O que converte é
**1 dashboard bonito + 1 repositório limpo + 1 narrativa clara**. Os 9 projetos são a *profundidade*
que sustenta a entrevista técnica; o *gancho* é o primeiro projeto bem-acabado. Por isso a Fase 1
já entrega algo empregável.

---

## 2. A base compartilhada — BanVic

**O negócio:** o BanVic tem 10 agências (físicas e digitais), ~1.000 clientes PF, 100 colaboradores,
~72 mil transações e 2.000 propostas de crédito. Os dados vivem em 8 CSVs crus, com problemas reais
de qualidade (coluna duplicada no IPCA, ruído de float em saldos, CEP/CPF inconsistentes, datas em
texto). A diretoria quer respostas confiáveis e recorrentes.

**As 8 perguntas de negócio (KPIs) — a "prova" que todo projeto responde:**
1. Saldo sob gestão por agência (e por tipo física/digital).
2. Volume e quantidade de transações por mês e por tipo (Pix, cartão, saque…).
3. Mix de transações por categoria (% do volume).
4. Conversão de propostas de crédito por status + valor financiado.
5. Ranking de agências (saldo e volume).
6. Carteira por colaborador (contas, saldo gerido, propostas).
7. Segmentação de clientes por faixa etária vs saldo.
8. Correção de valores pela inflação (IPCA).

**O modelo dimensional (star schema) — o destino comum (camada Gold):**
- **Dimensões:** `dim_cliente` (com faixa etária), `dim_agencia`, `dim_colaborador`, `dim_tempo`,
  `dim_tipo_transacao`.
- **Fatos:** `fato_transacoes`, `fato_contas`, `fato_propostas`.

**Decisões de modelagem fixadas no gabarito (não altere sem ajustar os 9 projetos):**
- **`fato_contas` grain = 1 linha por conta (999 linhas — snapshot corrente).** Representa o estado
  do saldo no momento da extração; histórico de saldo é derivado de `fato_transacoes`, não de
  `fato_contas`.
- **KPI #8 (IPCA):** mês-base = `ano_mes` mais recente em `ipca.csv`; fórmula:
  `valor_real = valor_nominal × indice_base / indice_mes`; `valor_nominal` = soma do valor absoluto
  de todas as transações do mês (entradas e saídas contadas igualmente).

> O contrato de dados completo (dicionário, regras de limpeza, modelo, gabarito de validação) está
> detalhado no plano da **Fundação** em `docs/superpowers/plans/2026-06-02-projeto-00-fundacao.md`.
> Recomendação de Tech Lead: **construa a Fundação como "Fase 0"** — ela é o gabarito que prova que
> os 9 projetos batem nos mesmos números.

---

## 3. Mapa do portfólio (visão rápida)

| # | Projeto | Stack-chave | Dificuldade | Tempo efetivo | Papel-alvo principal | Fase |
|---|---|---|:---:|---|---|:---:|
| 1 | SQL Puro | PostgreSQL, SQL | 3/10 | 1–2 sem | Analista de Dados / BI | 1 |
| 2 | Python + PostgreSQL | Python, Pandas | 4/10 | 1–2 sem | Eng. Dados Jr | 2 |
| 3 | Apache Hop | Apache Hop | 4/10 | ~1 sem | Eng. Dados Jr / ETL | 2 |
| 4 | Docker + Ambiente | Docker, Compose | 5/10 | 3–5 dias | Eng. Dados Jr (infra) | 1 (enabler) |
| 5 | Airflow + Python | Airflow | 6/10 | ~2 sem | Eng. Dados Jr | 2 |
| 6 | Modern Data Stack (dbt) | dbt | 6/10 | ~2 sem | **Analytics Engineer** | 3 |
| 7 | Databricks Lakehouse | PySpark, Delta | 7/10 | 2–3 sem | Eng. Dados (Pleno) | 4 |
| 8 | n8n | n8n, APIs | 4/10 | ~1 sem | Automação / Analista | 4 |
| 9 | Microsoft Fabric | Fabric, Power BI | 6/10 | ~2 sem | BI / Analytics Eng | 3 |

Total: ~14–20 semanas de trabalho efetivo, distribuídas em 12 meses (sobra tempo para aprofundar,
documentar e postar — depth > breadth).

---

## 4. Roadmap em 4 fases (12 meses)

**Fase 1 — Fundação + empregabilidade rápida (meses 1–3).**
Projetos: **Fundação (Fase 0)** → **P1 SQL Puro** → **P4 Docker** → primeiro **dashboard** (Power BI
Desktop ou Metabase) sobre o DW.
Resultado: já te posiciona para **Analista de Dados / BI**. É a fase do "gancho".
*Crítica:* não pule o dashboard — é o que recrutador vê em 10 segundos.

**Fase 2 — ETL e engenharia júnior (meses 4–6).**
Projetos: **P2 Python+PostgreSQL** → **P3 Apache Hop** → **P5 Airflow**.
Resultado: mostra que você **automatiza e orquestra** pipelines. Alvo: **Eng. de Dados Júnior**.

**Fase 3 — Analytics Engineering moderno (meses 7–9).**
Projetos: **P6 dbt** → **P9 Microsoft Fabric**.
Resultado: o combo mais quente do mercado atual (dbt + camada semântica + BI). Alvo:
**Analytics Engineer**.

**Fase 4 — Lakehouse, integração e consolidação (meses 10–12).**
Projetos: **P7 Databricks** → **P8 n8n** → **Dashboard Executivo** → **Capstone comparativo** +
consolidação (README-hub, vídeos, posts, currículo).
Resultado: fecha como **Engenheiro de Dados** com visão de plataforma — e com um dashboard que
um diretor de banco consegue abrir e usar.

> **Resequenciamento crítico:** embora numerado como #4, faça o **Docker cedo** (junto da Fase 1),
> porque todos os projetos seguintes rodam melhor containerizados. Docker é *enabler*, não destino.

---

## 5. Padrão comum a todos os projetos

**Estrutura de README (storytelling obrigatório), nesta ordem:**
`Problema de Negócio → Arquitetura → Tecnologias → Implementação → Resultados → Aprendizados →
Melhorias Futuras`.

**Práticas de engenharia que diferenciam júnior de "júnior bom" (aplicar em todos):**
- Git com commits pequenos e mensagens claras; branch por feature.
- `README.md` com diagrama, instruções de "1 comando para rodar" (Docker) e prints de resultado.
- Testes/validação contra o **gabarito** da Fundação (prova de correção).
- `.env.example` (nunca segredos no repo); dados-fonte montados somente leitura.
- Diagramas em **Mermaid** (versionáveis) + um diagrama "bonito" para o LinkedIn.
- Script `validate.py` (ou `validate.sql`) que chama `validar_gold()` da Fundação — **obrigatório
  em todos os projetos** como prova automática de correção contra o gabarito.
- `.github/workflows/ci.yml` com GitHub Actions rodando os testes **a partir do P1** — mesmo que
  seja só subir o Postgres em container, rodar os scripts SQL e executar `validate.py`. Badge verde
  no README é sinal imediato de profissionalismo (grátis para repos públicos).
- **Dashboard Power BI único e acumulativo** (`dashboard/BanVic.pbix`): um único arquivo `.pbix`
  vive na raiz do monorepo. Cada projeto aponta sua fonte de dados para ele — o visual e as 8
  métricas permanecem iguais. Isso prova ao recrutador, visualmente, que a tese é real: "mesma
  pergunta de negócio, qualquer tecnologia, mesmo resultado."

---

## 6. Detalhamento dos 9 projetos

> Cada projeto traz os 15 itens solicitados. "Competências currículo/LinkedIn" estão escritas para
> você copiar e colar.

### Projeto 1 — SQL Puro (DW + Modelagem Dimensional)

1. **Objetivo de negócio:** entregar à diretoria do BanVic um Data Warehouse confiável que responde
   as 8 perguntas via SQL, sem depender de planilhas manuais.
2. **Objetivo técnico:** dominar SQL analítico e modelagem dimensional (Kimball): staging → fatos →
   dimensões → star schema.
3. **Arquitetura:** PostgreSQL com 3 schemas — `staging` (raw 1:1 dos CSVs), `intermediate`
   (limpeza/conformação) e `dw` (star schema). Tudo via scripts SQL versionados e idempotentes.
   GitHub Actions: a cada push, o workflow sobe Postgres em container, executa os scripts em ordem
   e roda `validate.py` contra o gabarito da Fundação.
4. **Fluxo de dados:** `COPY` dos CSVs → `staging` → views/CTAS de limpeza → `intermediate` →
   `INSERT ... SELECT` → `dw.dim_*` e `dw.fato_*` → views de KPI.
5. **Estrutura de pastas:**
   ```
   projeto-01-sql-puro/
     sql/00_staging/  01_intermediate/  02_dw/  03_kpis/
     docs/  validacao/  README.md
   ```
6. **Tecnologias:** PostgreSQL, SQL (DDL, DML, CTE, window functions), psql/`COPY`, GitHub Actions.
7. **Dificuldade:** 3/10.
8. **Tempo estimado:** 1–2 semanas.
9. **Currículo:** "Modelagem dimensional (star schema, Kimball); construção de Data Warehouse em
   PostgreSQL; SQL analítico avançado (CTEs, window functions); SQL idempotente e versionado."
10. **LinkedIn:** "Construí um Data Warehouse do zero em SQL puro: do CSV cru ao star schema, com 8
    KPIs de negócio. Sem ferramenta mágica — só modelagem bem-feita."
11. **GitHub:** README com o diagrama do star schema, o DER, um GIF/print das queries de KPI
    rodando e o **badge verde do GitHub Actions**. Scripts numerados na ordem de execução. Conecta
    ao `dashboard/BanVic.pbix` — primeira versão do dashboard compartilhado com os 8 KPIs.
12. **Diagramas:** DER (entidade-relacionamento) da fonte + star schema (Mermaid `erDiagram`) +
    fluxo de camadas.
13. **Evidências:** print do star schema no DBeaver, resultados das 8 queries de KPI, prova de
    idempotência (rodar 2x = mesmo resultado).
14. **Entrevista:** "Por que separei staging de DW? Por que escolhi grão de transação no fato?
    Como garanti idempotência?" — tenha a resposta de cada decisão de modelagem.
15. **Evoluções:** SCD Tipo 2 nas dimensões; particionamento do fato de transações; índices e
    `EXPLAIN ANALYZE` para performance.

---

### Projeto 2 — Python + PostgreSQL (ETL tradicional via código)

1. **Objetivo de negócio:** automatizar a carga do DW do BanVic com um pipeline reexecutável, com
   logs auditáveis (a diretoria confia em números rastreáveis).
2. **Objetivo técnico:** ETL imperativo — extração, transformação (Pandas) e carga, com logging,
   tratamento de erros e configuração externalizada.
3. **Arquitetura:** scripts Python modulares (`extract`/`transform`/`load`) + SQLAlchemy para o
   Postgres; configuração via `.env`; logs estruturados.
4. **Fluxo:** ler CSVs → DataFrames → limpeza/conformação (mesmo contrato da Fundação) → construir
   dims/fatos → `to_sql` no Postgres → validação contra gabarito.
5. **Estrutura de pastas:**
   ```
   projeto-02-python-postgres/
     src/{extract,transform,load,config}.py  main.py
     tests/  logs/  docker-compose.yml  README.md
   ```
6. **Tecnologias:** Python, Pandas, SQLAlchemy, psycopg2, logging, pytest.
7. **Dificuldade:** 4/10.
8. **Tempo:** 1–2 semanas.
9. **Currículo:** "Pipelines ETL em Python/Pandas; carga em PostgreSQL via SQLAlchemy; logging e
   tratamento de erros; testes com pytest."
10. **LinkedIn:** "Reescrevi o DW do BanVic como um ETL em Python — modular, testado e com logs.
    SQL é ótimo para transformar; Python brilha na orquestração da extração e nas regras complexas."
11. **GitHub:** README com diagrama do pipeline, exemplo de log, e a comparação honesta "SQL puro vs
    Python" (quando usar cada um).
12. **Diagramas:** fluxo E-T-L com os módulos; diagrama de sequência da execução.
13. **Evidências:** trecho de log de uma execução, saída do pytest verde, print das tabelas no DW.
14. **Entrevista:** "Por que Pandas e não SQL para esta etapa? Como você trataria 100x mais dados?"
    (gancho para falar de chunking/Polars/Spark — conecta com P7).
15. **Evoluções:** trocar Pandas por Polars; processamento em chunks; cargas incrementais
    (upsert) em vez de full-load.

---

### Projeto 3 — Apache Hop (ETL visual / low-code)

1. **Objetivo de negócio:** mostrar que o pipeline do BanVic pode ser mantido por analistas sem
   código pesado, reduzindo dependência de devs.
2. **Objetivo técnico:** construir o mesmo ETL de forma visual (pipelines e workflows), entendendo
   ferramentas low-code corporativas (Hop é o sucessor open-source do Pentaho/Kettle).
3. **Arquitetura:** Apache Hop (pipelines de transformação + workflows de orquestração) → Postgres.
4. **Fluxo:** input CSV → steps de limpeza/lookup/join → output table; um workflow encadeia as
   pipelines (dims antes dos fatos).
5. **Estrutura de pastas:**
   ```
   projeto-03-apache-hop/
     hop/{pipelines/*.hpl, workflows/*.hwf, metadata/}
     docs/  docker-compose.yml  README.md
   ```
6. **Tecnologias:** Apache Hop, PostgreSQL, JDBC.
7. **Dificuldade:** 4/10.
8. **Tempo:** ~1 semana.
9. **Currículo:** "ETL visual com Apache Hop (Pentaho-like); design de pipelines e workflows;
   integração com PostgreSQL via JDBC."
10. **LinkedIn:** "Mesmo pipeline, zero linhas de código: refiz o ETL do BanVic no Apache Hop.
    Ferramentas visuais ainda dominam muito ambiente corporativo — vale ter no currículo."
11. **GitHub:** README com **screenshots dos pipelines** (o visual é o produto aqui) + export dos
    `.hpl/.hwf` versionados.
12. **Diagramas:** o próprio canvas do Hop é o diagrama; some um fluxo de alto nível.
13. **Evidências:** prints do canvas de cada pipeline, do workflow orquestrando, e métricas de
    execução (linhas processadas).
14. **Entrevista:** "Quando indicar low-code vs código? Como versionar e testar pipelines visuais?"
15. **Evoluções:** parametrização por ambiente; execução via `hop-run` em container (CI); logging
    em tabela de auditoria.

---

### Projeto 4 — Docker + Ambiente de Dados (plataforma reproduzível)

> **Reframe crítico (Tech Lead):** Docker raramente é um "projeto-destino" — é um *enabler*. Para
> ele valer no portfólio, posicione-o como **"a plataforma de dados local que roda todo o portfólio
> com um comando"**, não como "aprendi Docker".
> **Quando executar:** imediatamente após a Fundação (antes do P1), apesar da numeração #4. Está
> numerado assim por razões didáticas, mas pertence à Fase 1. Todos os projetos seguintes reutilizam
> o `docker-compose.yml` aqui criado.

1. **Objetivo de negócio:** qualquer pessoa do time consegue subir o ambiente analítico do BanVic em
   minutos, eliminando o "na minha máquina funciona".
2. **Objetivo técnico:** ambiente reproduzível com Docker Compose: Postgres + ferramenta de BI
   (Metabase) + (opcional) pgAdmin, com volumes, redes e seeds automáticos.
3. **Arquitetura:** `docker-compose.yml` orquestrando serviços; init scripts que carregam o DW;
   dados-fonte montados read-only; variáveis em `.env`.
4. **Fluxo:** `docker compose up` → Postgres sobe → scripts de init criam schemas e carregam dados →
   Metabase conecta → dashboard pronto.
5. **Estrutura de pastas:**
   ```
   projeto-04-docker-ambiente/
     docker-compose.yml  .env.example
     postgres/initdb/*.sql   metabase/   docs/  README.md
   ```
6. **Tecnologias:** Docker, Docker Compose, PostgreSQL, Metabase, (opcional) pgAdmin.
7. **Dificuldade:** 5/10.
8. **Tempo:** 3–5 dias.
9. **Currículo:** "Containerização de ambientes de dados com Docker/Compose; provisionamento
   automatizado (init scripts, volumes, redes); ambiente analítico reproduzível."
10. **LinkedIn:** "`docker compose up` e pronto: todo o ambiente analítico do BanVic (banco + BI)
    de pé em 2 minutos. Reprodutibilidade é a base de tudo em dados."
11. **GitHub:** README com o comando único, diagrama dos containers, e um GIF do ambiente subindo.
12. **Diagramas:** topologia dos containers (serviços, redes, volumes).
13. **Evidências:** GIF do `compose up`, print do Metabase conectado, `docker ps`.
14. **Entrevista:** "Como você garante reprodutibilidade entre dev e prod? Volumes vs bind mounts?
    Por que init scripts idempotentes?"
15. **Evoluções:** healthchecks e `depends_on` com condição; perfis (profiles) por ferramenta;
    publicar a imagem; evoluir para Dev Containers.

---

### Projeto 5 — Airflow + Python (orquestração)

1. **Objetivo de negócio:** garantir que o DW do BanVic atualize sozinho, no horário certo, com
   alertas quando algo falha — sem alguém rodar script à mão.
2. **Objetivo técnico:** orquestração com Airflow — DAGs, dependências, agendamento, retries,
   monitoramento e logs.
3. **Arquitetura:** Airflow (em Docker) com uma DAG que encapsula o ETL do P2 em tasks
   (extract → transform → load → validate), com retries e notificação em falha.
4. **Fluxo:** scheduler dispara a DAG → tasks rodam na ordem das dependências → validação contra
   gabarito como última task → alerta se falhar.
5. **Estrutura de pastas:**
   ```
   projeto-05-airflow/
     dags/banvic_etl_dag.py   plugins/  include/
     docker-compose.yml  docs/  README.md
   ```
6. **Tecnologias:** Apache Airflow, Python, PostgreSQL, Docker.
7. **Dificuldade:** 6/10.
8. **Tempo:** ~2 semanas.
9. **Currículo:** "Orquestração de pipelines com Apache Airflow (DAGs, scheduling, retries,
   alerting, monitoramento); deploy do Airflow em Docker."
10. **LinkedIn:** "Coloquei o pipeline do BanVic no piloto automático com Airflow: agendado, com
    retries e alerta em falha. Orquestração é o que separa script de pipeline de produção."
11. **GitHub:** README com print da DAG no Graph View, explicação das dependências e da estratégia
    de retry/alerta.
12. **Diagramas:** o DAG graph (print) + diagrama de agendamento/SLA.
13. **Evidências:** print do Graph/Grid View, log de uma execução com retry, e-mail/Slack de alerta.
14. **Entrevista:** "Idempotência de tasks, backfill, catchup, XComs, por que não usar Airflow para
    streaming." Saiba responder.
15. **Evoluções:** sensores (esperar arquivo chegar); cargas incrementais com `data_interval`;
    migrar para TaskFlow API; observabilidade com métricas.

---

### Projeto 6 — Modern Data Stack / dbt (Analytics Engineering)

> Este é o projeto **mais valioso para o mercado atual** (Analytics Engineer). Capriche.

1. **Objetivo de negócio:** entregar métricas do BanVic confiáveis, testadas e documentadas, que o
   time de BI consome sem retrabalho.
2. **Objetivo técnico:** ELT com dbt — transformação declarativa em SQL no banco, com testes,
   documentação automática, lineage e camadas (staging → marts).
3. **Arquitetura:** dados crus carregados no Postgres (ou BigQuery) → dbt cria models em camadas
   (`stg_` → `int_` → `marts/`); testes (`unique`, `not_null`, `relationships`); `sources.yml` com
   `freshness` checks (alerta se os dados pararem de chegar — padrão cobrado em entrevista de
   Analytics Engineer); `dbt docs` com lineage.
4. **Fluxo:** `dbt seed/source` → `dbt run` (materializa models) → `dbt test` → `dbt docs generate`
   → camada de marts = os 8 KPIs.
5. **Estrutura de pastas:**
   ```
   projeto-06-dbt/
     models/{staging,intermediate,marts}/  tests/  macros/  seeds/
     dbt_project.yml  profiles.yml.example  README.md
   ```
6. **Tecnologias:** dbt-core, PostgreSQL (ou BigQuery sandbox), Jinja, SQL.
7. **Dificuldade:** 6/10.
8. **Tempo:** ~2 semanas.
9. **Currículo:** "Analytics Engineering com dbt (modelagem em camadas, testes de dados, source
   freshness, lineage, documentação); ELT em PostgreSQL/BigQuery; SQL + Jinja."
10. **LinkedIn:** "Transformei os dados do BanVic com dbt: SQL versionado, testado e documentado,
    com lineage automático. Analytics Engineering é SQL com práticas de engenharia de software."
11. **GitHub:** README com print do **lineage graph** (`dbt docs`), exemplos de testes, e link para
    a doc gerada (pode publicar no GitHub Pages).
12. **Diagramas:** o DAG/lineage do dbt + as camadas staging→marts.
13. **Evidências:** `dbt docs` (lineage), saída de `dbt test` (todos passando), screenshot dos marts.
14. **Entrevista:** "Materializações (view/table/incremental), testes genéricos vs singulares,
    sources vs seeds, por que camadas." Domine o vocabulário.
15. **Evoluções:** modelos incrementais; `dbt-expectations`; CI com `dbt build` no GitHub Actions;
    exposures conectando aos dashboards.

---

### Projeto 7 — Databricks Lakehouse (Arquitetura Medalhão)

1. **Objetivo de negócio:** preparar o BanVic para escala — processar milhões de transações com
   governança e histórico, não só os 72 mil atuais.
2. **Objetivo técnico:** Lakehouse com PySpark + Delta Lake na arquitetura medalhão
   (Bronze → Silver → Gold), com transações ACID e time travel. **Ângulo único vs P9 (Fabric):**
   o foco aqui é no *motor e no código* — você controla schema evolution, otimiza com Z-Order e
   usa time travel como auditoria via PySpark. P9 abstrai tudo isso numa plataforma gerenciada; P7
   mostra o que está por baixo.
3. **Arquitetura:** Databricks (Free Edition) com notebooks PySpark; tabelas Delta nas 3 camadas;
   (opcional) Unity Catalog para governança.
4. **Fluxo:** ingest CSV → **Bronze** (raw Delta) → **Silver** (limpo/conformado) → **Gold**
   (dims/fatos + KPIs) → consultas Spark SQL.
5. **Estrutura de pastas:**
   ```
   projeto-07-databricks-lakehouse/
     notebooks/{01_bronze,02_silver,03_gold}.py
     docs/  README.md   (+ fallback: docker com PySpark local)
   ```
6. **Tecnologias:** Databricks, PySpark, Spark SQL, Delta Lake.
7. **Dificuldade:** 7/10.
8. **Tempo:** 2–3 semanas.
9. **Currículo:** "Lakehouse com Databricks + Delta Lake; processamento distribuído com PySpark;
   arquitetura medalhão (Bronze/Silver/Gold); Spark SQL."
10. **LinkedIn:** "Levei o BanVic para um Lakehouse: PySpark + Delta Lake na arquitetura medalhão,
    com ACID e time travel. É assim que se processa dado em escala hoje."
11. **GitHub:** README com diagrama medalhão, prints dos notebooks e exemplo de **time travel**
    (`VERSION AS OF`). Exporte os notebooks como `.py`.
12. **Diagramas:** arquitetura medalhão (Bronze/Silver/Gold) + fluxo Spark.
13. **Evidências:** prints dos notebooks, do Delta time travel, e do plano de execução Spark.
14. **Entrevista:** "Por que Delta e não Parquet puro? Schema evolution, OPTIMIZE/Z-ORDER,
    narrow vs wide transformations, shuffle." Conecte com a pergunta de escala do P2.
15. **Evoluções:** streaming com Auto Loader; otimização (Z-Order, partições); Unity Catalog para
    governança e linhagem.

---

### Projeto 8 — n8n (Automação e Integração)

1. **Objetivo de negócio:** integrar o BanVic com o mundo externo — enriquecer dados via API e
   disparar alertas automáticos (ex.: notificar quando uma agência cai de produção).
2. **Objetivo técnico:** automação low-code orientada a eventos: workflows que extraem, tratam,
   carregam e notificam, com integração a APIs.
3. **Arquitetura:** n8n (em Docker) com workflows: trigger (cron/webhook) → nodes de
   extração/transformação → Postgres → node de alerta (e-mail/Telegram/Slack).
4. **Fluxo:** agendamento → busca dados (CSV/API) → transforma → grava no DW → checa regra de
   negócio → envia alerta se necessário.
5. **Estrutura de pastas:**
   ```
   projeto-08-n8n/
     workflows/*.json   docker-compose.yml   docs/   README.md
   ```
6. **Tecnologias:** n8n, PostgreSQL, APIs REST, webhooks.
7. **Dificuldade:** 4/10.
8. **Tempo:** ~1 semana.
9. **Currículo:** "Automação e integração de dados com n8n; consumo de APIs REST; alertas
   orientados a eventos; workflows agendados."
10. **LinkedIn:** "Automatizei alertas do BanVic com n8n: quando uma métrica sai do esperado, o time
    é avisado na hora. Integração + automação = menos trabalho manual, mais valor."
11. **GitHub:** README com screenshots dos workflows + export dos `.json` (importáveis).
12. **Diagramas:** o canvas do workflow + diagrama de integração (fontes, n8n, destinos, alertas).
13. **Evidências:** print do workflow, de uma execução bem-sucedida, e do alerta recebido.
14. **Entrevista:** "Quando automação low-code resolve melhor que código? Como tratar falhas e
    reprocessamento em workflows orientados a evento?"
15. **Evoluções:** webhooks reais; enriquecimento via API pública (ex.: cotação/indicadores);
    retries e dead-letter; observabilidade dos workflows.

---

### Projeto 9 — Microsoft Fabric (Plataforma integrada + Power BI)

1. **Objetivo de negócio:** entregar à diretoria do BanVic um dashboard executivo numa plataforma
   integrada (ingestão → lakehouse → BI) sem costurar 5 ferramentas.
2. **Objetivo técnico:** conhecer uma plataforma SaaS de ponta a ponta: Data Factory (ingestão),
   Lakehouse (medalhão) e Power BI (visualização) no Microsoft Fabric. **Ângulo único vs P7
   (Databricks):** o foco aqui é na *plataforma e no acesso do negócio* — DirectLake elimina a
   cópia de dados para o Power BI (zero ETL extra); RLS controla segurança por perfil de usuário;
   o analista de BI acessa sem escrever uma linha de PySpark. P7 mostra o motor; P9 mostra como a
   empresa escala o acesso para quem não é engenheiro.
3. **Arquitetura:** pipeline do Fabric Data Factory → Lakehouse (Bronze/Silver/Gold) → dataset
   semântico → relatório Power BI.
4. **Fluxo:** ingestão dos CSVs → camadas no Lakehouse → modelo semântico → dashboard com os 8 KPIs.
5. **Estrutura de pastas:** (Fabric é SaaS; versione exports e doc)
   ```
   projeto-09-microsoft-fabric/
     fabric/{pipelines,notebooks,semantic-model}/  powerbi/*.pbix
     docs/  README.md   (+ fallback local: P6 dbt + Power BI)
   ```
6. **Tecnologias:** Microsoft Fabric, Data Factory, Lakehouse, Power BI (Desktop é grátis).
7. **Dificuldade:** 6/10.
8. **Tempo:** ~2 semanas.
9. **Currículo:** "Microsoft Fabric (Data Factory, Lakehouse); modelagem semântica e dashboards em
   Power BI; arquitetura medalhão em plataforma SaaS."
10. **LinkedIn:** "Montei o BanVic ponta a ponta no Microsoft Fabric: ingestão, Lakehouse e um
    dashboard executivo no Power BI. Plataformas integradas reduzem atrito — e entregam valor rápido."
11. **GitHub:** README com **o dashboard como imagem de capa** (é o que mais converte), diagrama da
    arquitetura Fabric e o `.pbix` versionado.
12. **Diagramas:** arquitetura Fabric (Data Factory → Lakehouse → Power BI) + modelo semântico.
13. **Evidências:** screenshot do dashboard (caprichado), do pipeline no Fabric, do Lakehouse.
14. **Entrevista:** "Fabric vs Databricks vs stack open-source? Custo/lock-in? DirectLake vs
    Import?" Mostre que pensa em trade-offs de plataforma.
15. **Evoluções:** atualização incremental; RLS (row-level security) no Power BI; alertas de dados;
    comparar custo Fabric vs o fallback open-source.

---

## 7. Estratégia transversal: GitHub, LinkedIn, currículo e entrevistas

**GitHub (decisão de arquiteto):** use **um monorepo** `portfolio-banvic` com uma pasta por projeto
e um **README-hub** na raiz (a "vitrine") que linka os 9, mostra a tabela comparativa e exibe o
dashboard. Fixe (pin) esse repo no perfil. Alternativa: repositórios separados + um repo "índice".
Monorepo vence para contar a tese de "uma base, 9 stacks".

**LinkedIn (cadência):** 1 post por projeto concluído (não acumule). Estrutura do post: problema →
o que construí → 1 print/diagrama → 1 aprendizado → link. Faça 1 **carrossel** comparativo no fim
(o capstone). Frequência ~ a cada 2–3 semanas mantém você visível sem virar spam.

**Currículo:** uma seção "Portfólio de Engenharia de Dados (BanVic)" com 3–4 bullets de impacto
(não liste 9 projetos). Ex.: "Construí um DW dimensional e 8 pipelines (SQL, Python, dbt, Spark,
Airflow) sobre a mesma base bancária, validados contra um gabarito comum." Link para o repo.

**Power BI — o dashboard acumulativo (`dashboard/BanVic.pbix`):** mantenha um único arquivo na
raiz do monorepo. A cada projeto concluído, você atualiza a conexão (apontando para o novo banco ou
camada Gold) e tira um novo screenshot. O visual e as 8 métricas permanecem idênticos. Ao final,
você tem uma sequência: "aqui está o mesmo dashboard conectado a SQL puro, depois ao Python, depois
ao dbt, depois ao Databricks — e os números nunca mudam." Isso materializa a tese de portfólio em
algo que qualquer pessoa consegue ver sem ler uma linha de código. Use o Power BI Desktop (grátis).
Estrutura sugerida do `.pbix`: 5 abas — **Visão Geral**, **Agências**, **Clientes**, **Crédito**,
**Inflação (IPCA)**.

**Entrevistas (método):** para cada projeto, prepare uma história curta no formato
**Contexto → Decisão técnica → Trade-off → Resultado**. O entrevistador adora "por que você
escolheu X e não Y" — e seu portfólio foi *desenhado* para responder exatamente isso.

---

## 8. Análise crítica e riscos (visão de Tech Lead)

- **Risco nº 1 — repetição parecer preguiça.** Mitigação: o capstone comparativo (seção 9) e o
  ângulo único por projeto. Diga explicitamente "fiz de propósito, para comparar".
- **Risco nº 2 — largura sem profundidade.** 9 projetos rasos < 3 projetos profundos. Se o tempo
  apertar, **corte projetos, não qualidade**. Prioridade de impacto: **P1, P6, P9** (DW + dbt +
  dashboard) já fazem um portfólio empregável sozinhos.
- **Risco nº 3 — "tutorial portfolio".** Cada projeto precisa de **uma decisão sua** documentada
  (uma escolha de modelagem, uma otimização, um trade-off), não só "rodei a ferramenta".
- **Sobre o P4 (Docker):** sozinho é fraco como projeto. Forte como **a plataforma que roda os
  outros 8**. Reaproveite o Compose dele nos demais.
- **Custo/nuvem:** P7 (Databricks Free Edition) e P9 (Fabric trial 60 dias) não são grátis para
  sempre — tenha o **fallback local** documentado (P7→PySpark em Docker; P9→P6 dbt + Power BI).
- **Gabarito é full-load only:** o gabarito da Fundação cobre apenas carga completa. Se implementar
  cargas incrementais (P5/Airflow com `data_interval`, P6/dbt incremental, P7/Delta upsert), documente
  no README de cada projeto qual a estratégia de validação incremental — não há `validar_gold()`
  automático para esse caso.
- **Ordem de empregabilidade:** entregue **um dashboard já na Fase 1**. É o ativo que mais converte
  para Analista/BI e abre portas enquanto você constrói o resto.

---

## 9. Capstone — A Matriz Comparativa (o que amarra tudo)

Ao final, produza **um artigo/post + uma tabela** comparando as 9 abordagens na mesma base:

| Critério | SQL | Python | Hop | Airflow | dbt | Databricks | n8n | Fabric |
|---|---|---|---|---|---|---|---|---|
| Curva de aprendizado | | | | | | | | |
| Custo | | | | | | | | |
| Escala | | | | | | | | |
| Governança/testes | | | | | | | | |
| Manutenção | | | | | | | | |
| Quando usar | | | | | | | | |

Esse capstone é a peça que prova senioridade de raciocínio — é o que um Arquiteto entregaria.
Preencha-o com a sua experiência real ao longo dos 12 meses.

---

## 10. Dashboard Executivo — o ativo visual do portfólio

O dashboard acumulativo (`BanVic.pbix`) acompanhou todos os 9 projetos. Na Fase 4, você o
**refina** para nível executivo: não técnico, não acadêmico. Um diretor de banco, sem nenhum
conhecimento de dados, consegue abrir, navegar e entender sozinho.

**Estrutura (5 abas):**

| Aba | Conteúdo |
|---|---|
| **Visão Geral** | 8 KPIs em cards + gráfico de saldo e volume mensal (MoM, YoY) |
| **Agências** | Ranking, mapa ou treemap por saldo e volume; destaque digital vs físico |
| **Clientes** | Segmentação por faixa etária vs saldo; distribuição geográfica (UF) |
| **Crédito** | Funil de conversão de propostas; valor financiado por status e agência |
| **Inflação (IPCA)** | Volume nominal vs real por mês; impacto da inflação na carteira |

**Padrão de qualidade (o que distingue "bonito" de "profissional"):**
- Paleta de cores consistente em todo o arquivo (máximo 3 cores principais + neutros).
- KPIs com variação period-over-period (seta + %) em todos os cartões da Visão Geral.
- Tooltips em linguagem de negócio — "Saldo total gerido pela agência" em vez de "SUM(saldo_total)".
- Zero jargão técnico visível: nenhum nome de coluna, schema ou função aparece na tela.
- Título de página e descrição de contexto em cada aba (o diretor não precisa perguntar o que está vendo).
- Publicar no **Power BI Service** (conta grátis) para ter um link público compartilhável.

**Por que vale cada hora investida:** o dashboard executivo é o ativo que o recrutador
**mostra para a liderança** antes de te chamar. Um portfólio técnico impecável passa no filtro
técnico; um dashboard que a diretoria consegue usar passa no filtro de negócio. Com ambos, você
elimina a concorrência em dois momentos diferentes do processo seletivo.

---

## Próximos passos sugeridos
1. Corrigir o contrato SQL do modelo Gold e das oito views de KPI.
2. Implementar o **Projeto 1 (SQL Puro)** com carga PostgreSQL ponta a ponta.
3. Comparar automaticamente as views Gold com `docs/gabarito/gabarito.json`.
4. Criar o README principal, o setup reproduzível e a primeira versão do dashboard.
5. Adicionar testes e CI antes de iniciar a próxima stack.
