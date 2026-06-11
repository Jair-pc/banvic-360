# Projeto 1 — SQL Puro (PostgreSQL)

Este projeto resolve o pipeline inteiro do BanVic usando apenas SQL — sem Python, sem ferramentas extras, sem frameworks. Só o banco de dados fazendo tudo.

**Pergunta principal:** _Até onde SQL puro consegue ir?_

---

## O que acontece aqui

Imagine que os dados do banco chegaram bagunçados em tabelas brutas (Bronze). Este projeto pega esses dados, organiza em tabelas limpas (Silver) e monta o modelo final (Gold) — tudo usando instruções SQL direto no PostgreSQL.

No final, 8 perguntas são respondidas e verificadas contra o gabarito.

---

## Resultado

```
7/7 KPIs corretos — APROVADO
```

| KPI | Resposta | Status |
|---|---|---|
| 1 — Saldo por agência | R$ 26.509.620,12 | OK |
| 2/3 — Volume de transações | R$ 58.122.708,67 | OK |
| 4 — Propostas de crédito | 525 Enviada / 513 Aprovada | OK |
| 5 — Ranking de agências | Agência Digital em 1° | OK |
| 6 — Carteira por colaborador | Total R$ 26.509.620,12 | OK |
| 7 — Segmentação por idade | 50.997 clientes | OK |
| 8 — Correção IPCA | R$ 58.122.708,67 (nominal) | OK |

---

## Arquivos do projeto

```
projetos/01-sql-puro/sql/
├── 01_populate_dims.sql   Popula as 6 dimensões (clientes, agências, tempo...)
├── 02_populate_fatos.sql  Popula as 3 tabelas de fatos (transações, contas, propostas)
├── 03_indices.sql         Cria 17 índices para deixar as consultas mais rápidas
└── 04_kpis_analyze.sql    Calcula as 8 KPIs com análise de performance
```

---

## Como executar

Antes de começar, o banco precisa estar rodando com os dados carregados:

```bash
# Na raiz do projeto
docker compose up -d
python scripts/carga_bronze.py
```

Depois execute na ordem:

```bash
# 1. Preencher as dimensões (tabelas de referência)
psql -U banvic_user -d banvic -f projetos/01-sql-puro/sql/01_populate_dims.sql

# 2. Preencher os fatos (dados das transações, contas, propostas)
psql -U banvic_user -d banvic -f projetos/01-sql-puro/sql/02_populate_fatos.sql

# 3. Criar os índices (deixa as consultas mais rápidas)
psql -U banvic_user -d banvic -f projetos/01-sql-puro/sql/03_indices.sql

# 4. Verificar se as respostas estão corretas
python scripts/validar_gabarito_pg.py
```

---

## Por que esse projeto é importante

SQL puro é o ponto de partida de qualquer engenheiro de dados. Antes de aprender Airflow, dbt ou Databricks, você precisa dominar o SQL — porque todas essas ferramentas, no fundo, geram ou executam SQL.

Este projeto mostra que dá para fazer um pipeline completo só com SQL. Mas também mostra os limites: sem agendamento automático, sem retry em caso de falha, sem documentação automática, sem versionamento das transformações.

É exatamente esses problemas que os projetos seguintes resolvem.

---

## Técnicas de SQL usadas

| Técnica | Para que serve |
|---|---|
| Window Functions (`ROW_NUMBER OVER PARTITION BY`) | Encontrar o registro mais recente de cada cliente |
| CTEs (WITH ...) | Separar cálculos complexos antes de juntar tudo |
| Índices cobertos (`INCLUDE`) | Responder consultas sem nem acessar a tabela principal |
| Índices parciais (`WHERE eh_conta_ativa`) | Índice menor, só para os registros que importam |
| `ON CONFLICT DO NOTHING` | Inserir sem erro mesmo se o registro já existir |
| `EXPLAIN ANALYZE` | Ver quanto tempo cada consulta leva e por quê |
| Star Schema | Modelo de dados padrão para análises — fácil de entender e rápido |

---

## Performance das consultas (EXPLAIN ANALYZE)

Com os dados originais (~1.000 clientes, 72k transações):

| KPI | Tempo | Por quê é rápido |
|---|---|---|
| KPI 1 — Saldo por agência | 1,7 ms | Hash Join + índice coberto |
| KPI 2/3 — Volume transações | 179 ms | 72k linhas com índice composto |
| KPI 4 — Propostas | < 1 ms | Tabela pequena, busca sequencial |
| KPI 5 — Ranking | 2 ms | Reaproveita cálculo do KPI 1 |
| KPI 6 — Por colaborador | 3 ms | Dois índices, duas CTEs |
| KPI 7 — Por faixa etária | 45 ms | Índice parcial por faixa |
| KPI 8 — Correção IPCA | 195 ms | Window function + IPCA do período |

---

## Quando usar SQL Puro

| Situação | Faz sentido? |
|---|---|
| Time pequeno que já sabe SQL bem | Sim — zero dependências extras |
| Pipeline simples (carga → transforma → entrega) | Sim — menos partes = menos problemas |
| Precisar de retry automático e alertas | Não — use Airflow (Projeto 5) |
| Precisar de testes e documentação automáticos | Não — use dbt (Projeto 6) |
| Dados acima de 100 GB | Não — use Databricks (Projeto 7) |
