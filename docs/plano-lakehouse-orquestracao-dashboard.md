# BanVic 360 -- Fases 15, 16, 17 e 18

## Fase 15 -- Arquitetura Lakehouse

### Visao geral

```
FONTES EXTERNAS          INGESTAO              ARMAZENAMENTO         CONSUMO
─────────────────        ──────────            ─────────────         ───────
BCB (API REST)    ─┐
IBGE (API REST)   ─┤     scripts/             Bronze (raw)
BrasilAPI         ─┤  download_datasets.py    Silver (clean)   ──>  Gold DW
Open-Meteo        ─┘                          Gold (star)           Views KPI

CSVs BanVic       ─┐     COPY /               Bronze tables
Dados sinteticos  ─┘     carga_bronze.sql     Silver transforms

                          Airflow DAGs         Delta Lake           Power BI
                          Apache Hop           (Databricks)         dbt metrics
                          n8n webhooks         Fabric Lakehouse
```

### Camadas e responsabilidades

| Camada | Schema | Responsabilidade | Formato |
|---|---|---|---|
| Bronze | `bronze.*` | Ingestao bruta, TEXT, imutavel | CSV -> PostgreSQL/Delta |
| Silver | `silver.*` | Tipagem, limpeza, DQ, enriquecimento | tabelas tipadas |
| Gold | `gold.*` | Star schema, dimensoes, fatos, KPI views | star schema |
| DQ | `dq.*` | Log de qualidade, scorecard, auditoria | audit_log table |

### Compatibilidade multi-stack

| Stack | Bronze | Silver | Gold |
|---|---|---|---|
| PostgreSQL (Projetos 1-2) | COPY CSV | CREATE TABLE AS SELECT | DDL existente |
| Apache Hop (Projeto 3) | File Input transform | Mapping transforms | Table Output |
| Airflow (Projeto 5) | PythonOperator + COPY | SQLExecuteQueryOperator | trigger DAGs |
| dbt (Projeto 6) | seeds / sources | models (staging) | models (marts) |
| Databricks (Projeto 7) | Auto Loader (CSV) | Delta tables (bronze/silver) | Delta Gold |
| Microsoft Fabric (Projeto 9) | Dataflow / Lakehouse | Notebook (PySpark) | Semantic model |

### Delta Lake (Databricks/Fabric)

```
banvic_lakehouse/
  _bronze/
    banvic_original/     <- Delta tables das 7 tabelas originais
    sintetico/           <- Delta tables dos 10 arquivos sinteticos
    external/            <- Delta tables dos 14 datasets + projecoes
  _silver/
    entidades/           <- clientes, contas, agencias, colaboradores
    transacional/        <- transacoes, propostas, cartoes, investimentos
    macro/               <- ipca, selic, cdi, municipios
  _gold/
    dim_*/               <- 9 dimensoes
    fato_*/              <- 9 fatos
    kpis/                <- views/tabelas materializadas dos 8 KPIs
```

### Lineage resumido

```
bronze.transacoes
  -> silver.transacoes_clean  (tipagem + canal derivado)
    -> gold.fato_transacoes   (join dim_tempo + dim_cliente + dim_agencia)
      -> gold.vw_kpi2_3_...   (volume e mix por mes)
      -> gold.vw_kpi8_...     (correcao IPCA)

bronze.ipca + bronze.ipca_projetado
  -> silver.ipca_clean        (real + projecao unificados)
    -> gold.dim_tempo         (indice_ipca por dia)
      -> gold.vw_kpi8_...
```

---

## Fase 16 -- Orquestracao

### Hierarquia de dependencias (DAG order)

```
[1] download_datasets.py       -> bronze (dados externos)
[2] expandir_agencias.py       -> data/sintetico/agencias
[3] expandir_colaboradores.py  -> data/sintetico/colaboradores
[4] gerar_dados_sinteticos.py  -> data/sintetico/* (ordem: cli -> contas -> tx)
[5] projetar_series_historicas -> external_data/projecoes/
[6] carga_bronze.sql           -> bronze.* (todos os CSVs)
[7] data_quality_framework.sql -> dq.audit_log (validacao)
[8] ddl_silver_transforms.sql  -> silver.* (se DQ OK)
[9] ddl_modelo_dimensional.sql -> gold.* (dims + fatos)
[10] validar_gabarito.py       -> docs/gabarito/ (verificacao final)
```

### Airflow (Projeto 5) -- DAGs planejadas

| DAG | Schedule | Descricao |
|---|---|---|
| `dag_ingestao_macro` | `0 6 * * 1` (seg) | Baixa Selic, CDI, PTAX da semana |
| `dag_ingestao_ibge` | `0 3 1 * *` (mensal) | IPCA + municipios |
| `dag_carga_bronze` | `@once` / trigger | COPY de todos os CSVs |
| `dag_silver_transforms` | trigger apos bronze | Executa ddl_silver_transforms.sql |
| `dag_gold_refresh` | trigger apos silver | Refresha dims e fatos |
| `dag_dq_scorecard` | diario | Executa DQ e alerta se erros |
| `dag_gabarito` | semanal | valida_gabarito.py e compara resultados |

### Apache Hop (Projeto 3) -- Workflows

```
main_pipeline.hwf
  |- 01_ingestao/
  |    |- download_macro.hwf
  |    |- download_ibge.hwf
  |- 02_bronze/
  |    |- load_banvic.hwf         (File Input -> Table Output)
  |    |- load_sintetico.hwf
  |    |- load_external.hwf
  |- 03_silver/
  |    |- transform_clientes.hwf  (tipagem + derivados)
  |    |- transform_transacoes.hwf
  |    |- transform_macro.hwf
  |- 04_gold/
  |    |- load_dims.hwf
  |    |- load_fatos.hwf
  |- 05_dq/
       |- validar_qualidade.hwf
       |- alertar_erros.hwf
```

### n8n (Projeto 8) -- Automacoes

| Workflow | Trigger | Acao |
|---|---|---|
| Alerta DQ | Cron diario | Consulta dq.scorecard -> email se ERROR > 0 |
| Novo dataset | Webhook | Dispara carga_bronze.sql para tabela especifica |
| Status gabarito | Cron semanal | Compara KPIs e alerta desvios |
| Monitor Selic | Cron diario | Verifica se Selic mudou -> atualiza dim_tempo |

---

## Fase 17 -- Dashboard Executivo (Power BI)

### Estrutura de abas

| Aba | Paginas | KPIs principais |
|---|---|---|
| **Visao Geral** | Home executivo | Clientes totais, saldo total, receita mes |
| **Agencias** | Mapa + ranking + performance | KPI 1, KPI 5 |
| **Credito** | Propostas + aprovacao + inadimplencia | KPI 4, NPL, taxa recuperacao |
| **Transacoes** | Volume mensal + mix + sazonalidade | KPI 2, KPI 3 |
| **Carteira** | Por colaborador + faixa etaria | KPI 6, KPI 7 |
| **Investimentos** | Patrimonio + rentabilidade + mix | Patrimonio ativo, ticket medio |
| **Seguros** | Apolices + receita + sinistralidade | Cross-sell, conversao |
| **Fraudes** | Mapa + horario + tipo + valor | Taxa fraude, recuperacao |
| **Economia** | Selic, IPCA, CDI, PTAX + correcao | KPI 8, correlacoes |
| **Crescimento** | Timeline 2023-2026 | Clientes, agencias, receita YoY |

### Medidas DAX essenciais (Power BI)

```dax
-- Saldo sob gestao (KPI 1)
Saldo Total = SUM(fato_contas[saldo_total])

-- Volume transacoes (KPI 2)
Volume Transacoes = SUM(fato_transacoes[valor_absoluto])

-- Taxa de aprovacao (KPI 4)
Taxa Aprovacao =
    DIVIDE(
        COUNTROWS(FILTER(fato_propostas, fato_propostas[status_proposta] = "Aprovada")),
        COUNTROWS(fato_propostas)
    )

-- Correcao IPCA (KPI 8)
Volume Real IPCA =
    SUMX(
        fato_transacoes,
        fato_transacoes[valor_absoluto]
            * RELATED(dim_tempo[indice_ipca_base])
            / RELATED(dim_tempo[indice_ipca])
    )

-- NPL Ratio
NPL Ratio =
    DIVIDE(
        SUMX(FILTER(fato_inadimplencia, fato_inadimplencia[dias_atraso] > 90), [valor_aberto]),
        SUM(fato_contas[saldo_total])
    )
```

### Conexao Power BI -> PostgreSQL

```
Servidor: localhost (ou host do PostgreSQL)
Banco: banvic
Schema: gold
Modo: DirectQuery (para dados atualizados) ou Import (performance)
Tabelas: todas as gold.dim_* e gold.fato_* + views gold.vw_kpi*
```

---

## Fase 18 -- Analises Avancadas de Negocio

### 18.1 Crescimento de clientes vs populacao IBGE

```sql
-- Penetracao do banco por municipio
SELECT
    m.municipio, m.uf, m.regiao,
    m.populacao,
    COUNT(DISTINCT c.sk_cliente) AS clientes_banvic,
    ROUND(COUNT(DISTINCT c.sk_cliente)::NUMERIC / NULLIF(m.populacao, 0) * 100, 4)
        AS penetracao_pct
FROM gold.dim_municipio m
LEFT JOIN gold.dim_cliente c ON c.sk_municipio = m.sk_municipio AND c.eh_registro_atual
GROUP BY m.municipio, m.uf, m.regiao, m.populacao
ORDER BY penetracao_pct DESC;
```

### 18.2 Credito vs PIB per capita municipal

```sql
-- Propensao ao credito por riqueza do municipio
SELECT
    m.municipio, m.uf,
    m.pib_per_capita,
    m.faixa_pib_per_cap,
    COUNT(fp.sk_proposta)       AS total_propostas,
    AVG(fp.valor_proposta)      AS ticket_medio,
    ROUND(AVG(CASE WHEN fp.status_proposta = 'Aprovada' THEN 1 ELSE 0 END) * 100, 2)
                                AS taxa_aprovacao_pct
FROM gold.dim_municipio m
JOIN gold.dim_cliente c   ON c.sk_municipio = m.sk_municipio
JOIN gold.fato_propostas_credito fp ON fp.sk_cliente = c.sk_cliente
GROUP BY m.municipio, m.uf, m.pib_per_capita, m.faixa_pib_per_cap
ORDER BY taxa_aprovacao_pct DESC;
```

### 18.3 Receita vs variacao Selic

```sql
-- Correlacao entre receita de juros e Selic do mes
SELECT
    t.ano, t.mes, t.mes_nome,
    AVG(t.taxa_selic) * 252 * 100   AS selic_media_aa,
    SUM(r.valor_receita) FILTER (WHERE r.tipo_receita = 'Juros') AS receita_juros
FROM gold.fato_receitas r
JOIN gold.dim_tempo t ON t.sk_tempo = r.sk_tempo
GROUP BY t.ano, t.mes, t.mes_nome, t.taxa_selic
ORDER BY t.ano, t.mes;
```

### 18.4 Inadimplencia vs desemprego regional

```sql
-- NPL por regiao vs taxa de desemprego
WITH npl AS (
    SELECT
        a.regiao,
        SUM(fi.valor_aberto) AS carteira_inadimplente,
        COUNT(*) AS contratos_atraso
    FROM gold.fato_inadimplencia fi
    JOIN gold.dim_cliente c ON c.sk_cliente = fi.sk_cliente
    JOIN gold.dim_municipio m ON m.sk_municipio = c.sk_municipio
    JOIN gold.dim_agencia a ON a.regiao = m.regiao
    GROUP BY a.regiao
)
SELECT
    npl.regiao,
    npl.carteira_inadimplente,
    npl.contratos_atraso,
    -- Cruzar com desemprego da tabela macro (a implementar por regiao)
    npl.carteira_inadimplente / NULLIF(SUM(fc.saldo_total), 0) * 100 AS npl_ratio
FROM npl
JOIN gold.fato_contas fc ON 1=1  -- agrupado por regiao
GROUP BY npl.regiao, npl.carteira_inadimplente, npl.contratos_atraso;
```

### 18.5 Fraudes por regiao e horario

```sql
-- Heatmap de fraudes: regiao x faixa de horario
SELECT
    a.regiao,
    CASE
        WHEN EXTRACT(HOUR FROM ff.hora_ocorrencia::TIME) BETWEEN 0 AND 5  THEN '00-05h (madrugada)'
        WHEN EXTRACT(HOUR FROM ff.hora_ocorrencia::TIME) BETWEEN 6 AND 11 THEN '06-11h (manha)'
        WHEN EXTRACT(HOUR FROM ff.hora_ocorrencia::TIME) BETWEEN 12 AND 17 THEN '12-17h (tarde)'
        ELSE '18-23h (noite)'
    END AS faixa_horario,
    ff.tipo_fraude,
    COUNT(*) AS qtd_ocorrencias,
    SUM(ff.valor_fraude) AS valor_total,
    ROUND(AVG(CASE WHEN ff.flag_confirmada THEN 1 ELSE 0 END) * 100, 1) AS taxa_confirmacao_pct
FROM gold.fato_fraudes ff
JOIN gold.dim_agencia a ON a.sk_agencia = ff.sk_agencia
GROUP BY a.regiao, faixa_horario, ff.tipo_fraude
ORDER BY qtd_ocorrencias DESC;
```

### 18.6 ROI de novas agencias

```sql
-- Retorno das agencias abertas em cada ano
SELECT
    t_abertura.ano AS ano_abertura,
    a.tipo_agencia,
    a.regiao,
    COUNT(DISTINCT a.sk_agencia) AS qtd_agencias,
    SUM(fc.saldo_total) AS saldo_sob_gestao,
    SUM(fc.qtd_transacoes_mes) AS transacoes_total,
    ROUND(SUM(fc.saldo_total) / NULLIF(COUNT(DISTINCT a.sk_agencia), 0), 2) AS saldo_medio_por_agencia,
    ROUND(SUM(fc.saldo_total) / NULLIF(a.meta_comercial_mensal * COUNT(DISTINCT a.sk_agencia), 0) * 100, 1)
        AS pct_meta_atingida
FROM gold.dim_agencia a
JOIN gold.dim_tempo t_abertura ON t_abertura.data = a.data_abertura
JOIN gold.fato_contas fc ON fc.sk_agencia = a.sk_agencia
GROUP BY t_abertura.ano, a.tipo_agencia, a.regiao, a.meta_comercial_mensal
ORDER BY t_abertura.ano, saldo_sob_gestao DESC;
```

### 18.7 Impacto do clima nas transacoes

```sql
-- Volume de transacoes vs temperatura/chuva (por cidade com agencia)
SELECT
    t.ano, t.mes,
    a.cidade, a.uf,
    AVG(cl.temperatura_media) AS temp_media_mes,
    SUM(cl.precipitacao_mm)   AS precipitacao_total_mm,
    SUM(ft.valor_absoluto)    AS volume_transacoes,
    COUNT(ft.sk_transacao)    AS qtd_transacoes
FROM gold.fato_transacoes ft
JOIN gold.dim_tempo t    ON t.sk_tempo  = ft.sk_tempo
JOIN gold.dim_agencia a  ON a.sk_agencia = ft.sk_agencia
-- dim_clima a ser criada a partir de bronze.clima_historico
-- JOIN gold.dim_clima cl ON cl.codigo_ibge = a.codigo_ibge
--                       AND cl.ano = t.ano AND cl.mes = t.mes
JOIN bronze.clima_historico cl
  ON cl.uf = a.uf
  AND EXTRACT(YEAR FROM cl.data::DATE) = t.ano
  AND EXTRACT(MONTH FROM cl.data::DATE) = t.mes
GROUP BY t.ano, t.mes, a.cidade, a.uf, cl.temperatura_media, cl.precipitacao_mm
ORDER BY t.ano, t.mes, volume_transacoes DESC;
```
