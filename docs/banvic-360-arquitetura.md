# BanVic 360° — Arquitetura Completa da Plataforma Analítica Bancária

> **Versão:** 1.1 | **Data:** 2026-06-10  
> **Papel:** Arquiteto de Dados Sênior + Analytics Engineer + Consultor Financeiro  
> **Status dos datasets:** 14 fontes coletadas e 5 séries projetadas; renda é proxy, escolaridade é placeholder e clima está parcial

---

## 1. VISÃO GERAL DA PLATAFORMA

### O que é o BanVic 360°

O BanVic (Banco Vitória) é uma simulação corporativa completa de um banco nacional brasileiro
em crescimento acelerado (2023–2026). A plataforma é o artefato central de um portfólio de
Engenharia de Dados que demonstra competências em 9 stacks diferentes resolvendo o mesmo problema.

### Tese do portfólio
> "Um problema bancário real, resolvido de 9 formas diferentes — chegando sempre às mesmas
> respostas validadas por gabarito."

### Escala-alvo

| Dimensão | Baseline (2023) | Meta (2026) |
|---|---|---|
| Clientes | 998 | 50.000 |
| Agências | 10 | 100 |
| Colaboradores | 100 | 1.200 |
| Transações | 72.000 | 2.642.400 sintéticas |
| Propostas de crédito | 2.000 | 56.635 sintéticas |
| Domínios de dados | 2 | 10 |

---

## 2. DIAGNÓSTICO DO ESTADO ATUAL (Fase 1)

### 2.1 Inventário de tabelas internas

| Tabela | Linhas | Período | Chave PK | Qualidade |
|---|---|---|---|---|
| `clientes` | 998 | 2010–2023 | `cod_cliente` | ⚠️ Média |
| `contas` | 999 | 2011–2023 | `num_conta` | ⚠️ Média |
| `agencias` | 10 | 2010–2020 | `cod_agencia` | ⚠️ Baixa |
| `colaboradores` | 100 | — | `cod_colaborador` | ⚠️ Média |
| `colaborador_agencia` | 100 | — | (composta) | ✅ OK |
| `propostas_credito` | 2.000 | 2014–2023 | `cod_proposta` | ⚠️ Média |
| `transacoes` | 71.999 | 2010–2023 | `cod_transacao` | ✅ Boa |

### 2.2 Problemas de qualidade identificados

**clientes:**
- `endereco` em campo único (rua + bairro + CEP + cidade + UF juntos)
- Sem separação cidade/UF
- Sem renda, profissão, escolaridade, score de crédito
- `data_inclusao` com timezone UTC inconsistente
- CEP com e sem máscara (95140-704 e 27275674)
- Todos PF — sem PJ

**contas:**
- `saldo_total` com float ruidoso (ex: `2984.7614999999996`)
- Sem flag de conta ativa/encerrada
- `tipo_conta` repetindo tipo do cliente (PF/PJ) em vez do produto (corrente/poupança)

**agencias:**
- Encoding quebrado em nomes (Agência → Ag\xeancia)
- Apenas 5 UFs (SP, RS, RJ, SC, PE) — sem presença nacional
- Sem lat/lon, sem meta_comercial, sem código IBGE da cidade

**colaboradores:**
- Sem cargo, salário, data_admissão, data_demissão
- `endereco` em campo único igual aos clientes
- Sem departamento, sem hierarquia

**propostas_credito:**
- Status: ['Enviada', 'Aprovada', 'Em análise', 'Validação documentos'] — sem 'Reprovada'
- Sem data_aprovacao, sem data_reprovacao, sem motivo_recusa
- Sem flag de inadimplência posterior

**transacoes:**
- Sem coluna de canal separado (Pix está no `nome_transacao` junto com o tipo)
- Sem flag débito/crédito explícita (precisa inferir pelo sinal do valor)
- Sem `cod_cliente` direto (precisa JOIN com contas)

### 2.3 Limitações analíticas

1. Não é possível calcular inadimplência — não há flag de atraso
2. Não é possível segmentar por renda/profissão — campos inexistentes
3. Cobertura geográfica restrita a 5 UFs
4. Período longo (2010–2023) com dados esparsos — sem sazonalidade confiável
5. Volume insuficiente (72k tx) para análises estatísticas robustas

---

## 3. DOMÍNIOS DE NEGÓCIO (Fase 2)

### Mapa de domínios BanVic 360°

```
┌─────────────────────────────────────────────────────────────────┐
│                    BANVIC 360° — DOMÍNIOS                        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  CORE BANKING│  │   CRÉDITO    │  │ INVESTIMENTOS│           │
│  │──────────────│  │──────────────│  │──────────────│           │
│  │ Clientes     │  │ Propostas    │  │ CDB / LCI    │           │
│  │ Contas       │  │ Empréstimos  │  │ LCA / Fundos │           │
│  │ Agências     │  │ Financiamen. │  │ Tesouro      │           │
│  │ Colabor.     │  │ Inadimplência│  │ Previdência  │           │
│  │ Transações   │  │ Recuperação  │  │ ETF          │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   SEGUROS    │  │   CARTÕES    │  │   FRAUDES    │           │
│  │──────────────│  │──────────────│  │──────────────│           │
│  │ Vida         │  │ Crédito      │  │ Tentativas   │           │
│  │ Auto         │  │ Débito       │  │ Confirmadas  │           │
│  │ Residencial  │  │ Fatura       │  │ Valor recup. │           │
│  │ Empresarial  │  │ Parcelamento │  │ Canal/device │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ RECEITA BANC │  │  COBRANÇA    │  │  MACRO/GEO   │           │
│  │──────────────│  │──────────────│  │──────────────│           │
│  │ Juros        │  │ Renegociação │  │ Selic/IPCA   │           │
│  │ Tarifas      │  │ Recuperação  │  │ PTAX/CDI     │           │
│  │ Seguros      │  │ Write-off    │  │ PIB/Pop IBGE │           │
│  │ Investim.    │  │              │  │ Clima/Feriado│           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. ARQUITETURA LAKEHOUSE — BRONZE / SILVER / GOLD (Fase 15)

### Visão geral

```
FONTES EXTERNAS          INGESTÃO           PROCESSAMENTO       CONSUMO
─────────────────        ─────────          ─────────────       ───────
BCB (PTAX/Selic/IPCA) ──▶ BRONZE ──▶ SILVER ──▶ GOLD ──▶ Power BI
IBGE (Mun/Pop/PIB)    ──▶                                ──▶ Notebooks
BrasilAPI (Feriados)  ──▶                                ──▶ APIs
Open-Meteo (Clima)    ──▶                                ──▶ dbt models
INMET (Clima BR)      ──▶
CSVs Internos         ──▶
Dados Sintéticos      ──▶
```

### Camada Bronze — Dados brutos (imutáveis)

| Tabela Bronze | Fonte | Método | Frequência |
|---|---|---|---|
| `bronze_clientes` | data/banvic/clientes.csv | COPY / dbt seed | Uma vez |
| `bronze_contas` | data/banvic/contas.csv | COPY / dbt seed | Uma vez |
| `bronze_agencias` | data/banvic/agencias.csv | COPY / dbt seed | Uma vez |
| `bronze_colaboradores` | data/banvic/colaboradores.csv | COPY / dbt seed | Uma vez |
| `bronze_colab_agencia` | data/banvic/colaborador_agencia.csv | COPY | Uma vez |
| `bronze_propostas` | data/banvic/propostas_credito.csv | COPY / dbt seed | Uma vez |
| `bronze_transacoes` | data/banvic/transacoes.csv | COPY / dbt seed | Incremental |
| `bronze_ipca` | external_data/macroeconomia/ipca.csv | COPY | Mensal |
| `bronze_selic` | external_data/macroeconomia/selic.csv | COPY | Diária |
| `bronze_ptax` | external_data/macroeconomia/dolar_ptax.csv | COPY | Diária |
| `bronze_feriados` | external_data/calendario/feriados.csv | COPY | Anual |
| `bronze_municipios` | external_data/geografia/municipios.csv | COPY | Eventual |
| `bronze_populacao` | external_data/geografia/populacao.csv | COPY | Decenal |
| `bronze_pib_municipal` | external_data/geografia/pib_municipal.csv | COPY | Anual |
| `bronze_clima` | Open-Meteo API | Python script | Diária |
| `bronze_desemprego` | BCB SGS-24369 | Python script | Mensal |
| `bronze_cdi` | BCB SGS-12 | Python script | Diária |
| `bronze_igpm` | FGV via BCB SGS-189 | Python script | Mensal |

**Regras Bronze:**
- Dados NUNCA são alterados após ingestão
- Preservar encoding, nulos, erros originais
- Adicionar metadados: `_ingestao_ts`, `_fonte`, `_arquivo`
- Particionamento: por ano de ingestão

### Camada Silver — Dados tratados

| Tabela Silver | Origem | Transformações |
|---|---|---|
| `silver_clientes` | bronze_clientes | Parse endereço, separar cidade/UF, normalizar CPF, calcular idade |
| `silver_contas` | bronze_contas | Arredondar saldo, inferir tipo produto, flag ativa/encerrada |
| `silver_agencias` | bronze_agencias | Fix encoding, adicionar código IBGE, lat/lon via CEP |
| `silver_colaboradores` | bronze_colaboradores | Parse endereço, calcular tempo empresa |
| `silver_transacoes` | bronze_transacoes | Flag débito/crédito, normalizar canal, adicionar cod_cliente |
| `silver_propostas` | bronze_propostas | Calcular prazo real, flag de inadimplência futura |
| `silver_indicadores_macro` | bronze_ipca/selic/ptax/cdi/igpm | Unificar série temporal, calcular acumulados |
| `silver_municipios` | bronze_municipios/populacao/pib | Enriquecer com pop + PIB, calcular densidade |
| `silver_clima` | bronze_clima | Agregar por dia, calcular anomalias |

**Regras Silver:**
- Tipagem correta de todos os campos
- Remoção de duplicatas com critério documentado
- Nulos tratados com regra explícita (preencher, descartar ou manter)
- Campos novos derivados documentados
- Particionamento: por ano+mês

### Camada Gold — Modelo dimensional (star schema)

Ver Seção 5 — Modelo Dimensional Completo.

---

## 5. MODELO DIMENSIONAL COMPLETO (Fase 13)

### 5.1 Diagrama do Star Schema

```
                         ┌─────────────────┐
                         │   dim_tempo      │
                         │─────────────────│
                         │ sk_tempo (PK)   │
                         │ data            │
                         │ ano/tri/mes/sem  │
                         │ dia_semana       │
                         │ eh_feriado       │
                         │ nome_feriado     │
                         │ eh_dia_util      │
                         │ taxa_selic       │
                         │ cotacao_dolar    │
                         │ cotacao_euro     │
                         │ ipca_mensal      │
                         │ cdi_diario       │
                         └────────┬────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼────────┐    ┌──────────▼────────┐    ┌─────────▼────────┐
│  fato_transacoes│    │  fato_contas      │    │ fato_propostas   │
│─────────────────│    │─────────────────  │    │──────────────────│
│ sk_tempo        │    │ sk_tempo          │    │ sk_tempo_entrada  │
│ sk_cliente      │    │ sk_cliente        │    │ sk_tempo_decisao  │
│ sk_agencia      │    │ sk_agencia        │    │ sk_cliente        │
│ sk_canal        │    │ sk_colaborador    │    │ sk_colaborador    │
│ sk_tipo_transac │    │ sk_produto_conta  │    │ sk_produto_cred.  │
│ valor           │    │ saldo_total       │    │ valor_proposta    │
│ flag_credito    │    │ saldo_disponivel  │    │ valor_financ.     │
│ cod_transacao   │    │ qtd_transacoes    │    │ taxa_juros        │
└─────────────────┘    └───────────────────┘    │ status           │
                                                │ dias_decisao     │
                                                └──────────────────┘

┌─────────────────┐    ┌───────────────────┐    ┌──────────────────┐
│ fato_investim.  │    │  fato_cartoes     │    │  fato_seguros    │
│─────────────────│    │─────────────────  │    │──────────────────│
│ sk_tempo        │    │ sk_tempo          │    │ sk_tempo         │
│ sk_cliente      │    │ sk_cliente        │    │ sk_cliente       │
│ sk_produto_inv  │    │ sk_produto_cartao │    │ sk_produto_seg   │
│ valor_aplicado  │    │ limite_total      │    │ premio_mensal    │
│ valor_atual     │    │ gasto_mes         │    │ valor_sinistro   │
│ rentab_pct      │    │ valor_fatura      │    │ status_apolice   │
└─────────────────┘    │ dias_atraso       │    └──────────────────┘
                       └───────────────────┘

┌─────────────────┐    ┌───────────────────┐
│fato_inadimplenc.│    │  fato_fraudes     │
│─────────────────│    │─────────────────  │
│ sk_tempo        │    │ sk_tempo          │
│ sk_cliente      │    │ sk_cliente        │
│ sk_contrato     │    │ sk_canal          │
│ dias_atraso     │    │ sk_agencia        │
│ valor_aberto    │    │ valor             │
│ bucket          │    │ flag_confirmada   │
│ faixa_risco     │    │ valor_recuperado  │
└─────────────────┘    └───────────────────┘

                    ┌──────────────────────────┐
                    │    fato_receitas          │
                    │──────────────────────────│
                    │ sk_tempo                  │
                    │ sk_agencia                │
                    │ sk_produto                │
                    │ tipo_receita              │  ← juros/tarifa/seguro/investim.
                    │ valor_receita             │
                    │ valor_custo               │
                    │ margem                    │
                    └──────────────────────────┘
```

### 5.2 Dimensões — Definição de grão

| Dimensão | Grão | Linhas de referência |
|---|---|---|
| `dim_tempo` | 1 linha por dia, com indicadores econômicos | 2020–2026 |
| `dim_cliente` | 1 linha por versão do cliente (SCD2) | 50.000+ |
| `dim_agencia` | 1 linha por agência | 100 |
| `dim_colaborador` | 1 linha por colaborador | 1.200 |
| `dim_municipio` | 1 linha por município | 5.571 |
| `dim_produto` | 1 linha por produto bancário | 28 |
| `dim_canal` | 1 linha por canal | 12 |
| `dim_score_credito` | 1 linha por faixa de score | 5 |
| `dim_clima` | 1 linha por município e data disponível | depende da cobertura |

### 5.3 Fatos — Definição de grão

| Fato | Grão | Linhas de referência |
|---|---|---|
| `fato_transacoes` | 1 linha por transação | 2.642.400 |
| `fato_contas` | 1 linha por conta (snapshot corrente) | 70.121 |
| `fato_propostas_credito` | 1 linha por proposta | 56.635 |
| `fato_investimentos` | 1 linha por posição | 16.008 |
| `fato_cartoes` | 1 linha por fatura mensal | 537.694 |
| `fato_seguros` | 1 linha por apólice | 17.769 |
| `fato_inadimplencia` | 1 linha por contrato inadimplente | 468 |
| `fato_receitas` | 1 linha por tipo de receita, agência e mês | derivada na Gold |
| `fato_fraudes` | 1 linha por ocorrência | 1.400 |

---

## 6. PLANO DE EXPANSÃO HISTÓRICA (Fase 3)

### 6.1 Crescimento planejado

| Ano | Clientes | Agências | Colaboradores | Transações/mês | Novas regiões |
|---|---|---|---|---|---|
| 2023 | 998 → 1.000 | 10 | 100 | ~6.000 | SP, RJ, RS, SC, PE |
| 2024 | 5.000 | 20 | 180 | ~30.000 | + MG, PR, BA, DF |
| 2025 | 20.000 | 50 | 500 | ~150.000 | + GO, CE, PA, AM, MT |
| 2026 | 50.000 | 100 | 1.200 | ~400.000 | Cobertura nacional |

### 6.2 Metodologia de geração de crescimento

```python
# Fórmula de crescimento exponencial por cohort
def crescimento_clientes(base, taxa_anual, meses):
    return base * (1 + taxa_anual/12) ** meses

# Distribuição de transações por cliente (Pareto 80/20)
# 20% dos clientes fazem 80% das transações
# Distribuição lognormal para valores de transação
```

### 6.3 Expansão geográfica das agências (Fase 4)

| Região | 2023 | 2024 | 2025 | 2026 | Cidades-chave |
|---|---|---|---|---|---|
| Sudeste | 6 | 9 | 22 | 44 | SP, RJ, BH, Campinas, Santos |
| Sul | 2 | 4 | 10 | 18 | POA, FLN, Curitiba, Blumenau |
| Nordeste | 1 | 3 | 8 | 16 | Recife, Fortaleza, Salvador, Natal |
| Centro-Oeste | 0 | 2 | 6 | 12 | Brasília, Goiânia, Campo Grande |
| Norte | 0 | 1 | 4 | 8 | Manaus, Belém, Porto Velho |
| Digital | 1 | 1 | — | 2 | Nacional |
| **Total** | **10** | **20** | **50** | **100** | |

**Tipos de agência:**
- **Física:** Agência padrão com atendimento presencial
- **Digital:** Sem atendimento presencial, operações 100% online
- **Premium:** Atendimento exclusivo para clientes de alta renda (PF >R$10k/mês)
- **Corporate:** Atendimento a PJ e grandes empresas

---

## 7. DATASETS EXTERNOS — COMPLETO (Fases 5 e 6)

### 7.1 Datasets coletados

| Dataset | Arquivo | Status | Período |
|---|---|---|---|
| IPCA | `macroeconomia/ipca.csv` | ✅ Completo | 2010–2025 |
| Selic | `macroeconomia/selic.csv` | ✅ Completo | 2020–2024 |
| PTAX Dólar | `macroeconomia/dolar_ptax.csv` | ✅ Completo | 2020–2024 |
| Feriados | `calendario/feriados.csv` | ✅ Completo | 2020–2025 |
| Municípios | `geografia/municipios.csv` | ✅ Completo | Ref. 2023 |
| População | `geografia/populacao.csv` | ✅ Completo | Censo 2022 |
| PIB Municipal | `geografia/pib_municipal.csv` | ✅ Completo | 2021 |
| CDI | `macroeconomia/cdi.csv` | ✅ Completo | série disponível |
| IGP-M | `macroeconomia/igpm.csv` | ✅ Completo | série disponível |
| Desemprego | `macroeconomia/desemprego.csv` | ✅ Completo | BCB SGS-24369 |
| Euro PTAX | `macroeconomia/euro_ptax.csv` | ✅ Completo | período disponível |
| Renda municipal | `geografia/renda_municipal.csv` | ⚠ Proxy PIB/12 | referência disponível |
| Escolaridade | `geografia/escolaridade_municipal.csv` | ⚠ Placeholder | não usar como observado |
| Clima histórico | `clima/clima_historico.csv` | ⚠ Parcial | 91 de 99 cidades |

### 7.2 Estrutura de historização (Fase 6)

Para dados com defasagem (PIB 2021, Censo 2022), criar séries projetadas:

```python
# CAGR para projeção de população 2022-2026
def projeto_populacao(pop_2022, cagr=0.008):
    return {ano: round(pop_2022 * (1 + cagr) ** (ano - 2022))
            for ano in range(2022, 2027)}

# Projeção PIB usando deflator IPCA
def projeto_pib(pib_2021, ipca_anual):
    pib = pib_2021
    resultado = {2021: pib}
    for ano, ipca in enumerate(ipca_anual, start=2022):
        pib = round(pib * (1 + ipca/100))
        resultado[ano] = pib
    return resultado
```

### 7.3 Como baixar novamente

```bash
python scripts/download_datasets.py
python scripts/download_datasets.py --dataset ipca
python scripts/download_datasets.py --dataset clima
```

---

## 8. ESTRATÉGIA DE DADOS SINTÉTICOS (Fase 7)

### 8.1 Princípios

1. **Preservar distribuições** — usar os 998 clientes reais como "semente" (seed)
2. **Bootstrapping** — expandir a partir de padrões reais
3. **Sazonalidade** — manter picos de dezembro, Carnaval, férias
4. **Correlações** — renda ↔ saldo ↔ ticket médio ↔ score de crédito

### 8.2 Cronograma de geração

```
Etapa 1: Expandir clientes 998 → 50.000
  ├── Técnica: faker + pandas + distribuições paramétricas
  ├── Preservar: faixa etária, sexo, profissões bancárias
  └── Adicionar: renda, profissão, escolaridade, score, cod_ibge_cidade

Etapa 2: Criar contas para novos clientes
  ├── Ratio: 1,2 contas por cliente em média
  └── Tipos: corrente PF, poupança, corrente PJ, conta salário

Etapa 3: Gerar transações 72k → 3M+
  ├── Técnica: bootstrapping das 72k reais com variação temporal
  ├── Período: 2023-2026 com crescimento exponencial
  └── Sazonalidade: dezembro +40%, janeiro -15%, Carnaval -20%

Etapa 4: Criar propostas de crédito 2k → 100k
  ├── Correlação: score baixo → taxa alta + mais reprovações
  └── Produto mix: empréstimo pessoal, consignado, financiamento auto, imobiliário

Etapa 5: Gerar fatos de investimentos, seguros, cartões
  └── Penetração: 30% dos clientes com investimento, 20% com seguro
```

### 8.3 Volumes efetivamente gerados

| Tabela | Linhas |
|---|---|
| `clientes` | 50.000 |
| `contas` | 70.121 |
| `transacoes` | 2.642.400 |
| `propostas_credito` | 56.635 |
| `investimentos` | 16.008 |
| `cartoes` | 537.694 |
| `seguros` | 17.769 |
| `inadimplencia` | 468 |
| `fraudes` | 1.400 |

---

## 9. FRAMEWORK DE QUALIDADE DE DADOS (Fase 14)

### 9.1 Regras de validação

| Tabela | Campo | Regra | Ação |
|---|---|---|---|
| clientes | cpfcnpj | Dígitos verificadores válidos | Rejeitar |
| clientes | data_nascimento | Não futura; >18 anos para PF | Rejeitar |
| contas | saldo_total | Não nulo; permitir negativo (cheque especial) | Alertar se < -50k |
| transacoes | valor_transacao | ≠ 0 | Rejeitar |
| transacoes | data_transacao | ≤ data atual; ≥ data_abertura da conta | Rejeitar |
| agencias | cod_agencia | Chave referenciada existe | Rejeitar |
| propostas | taxa_juros_mensal | Entre 0 e 0.30 (0% a 30% a.m.) | Alertar |
| municipios | codigo_ibge | 7 dígitos | Rejeitar |

### 9.2 Métricas de qualidade (scorecard)

```sql
-- Completude
SELECT
    COUNT(*) AS total,
    COUNT(email) * 100.0 / COUNT(*) AS pct_email_preenchido,
    COUNT(cpfcnpj) * 100.0 / COUNT(*) AS pct_cpf_preenchido,
    COUNT(data_nascimento) * 100.0 / COUNT(*) AS pct_nascimento_preenchido
FROM silver_clientes;

-- Unicidade
SELECT cpfcnpj, COUNT(*) AS ocorrencias
FROM silver_clientes
GROUP BY cpfcnpj
HAVING COUNT(*) > 1;

-- Referencial
SELECT t.num_conta
FROM bronze_transacoes t
LEFT JOIN bronze_contas c ON c.num_conta = t.num_conta
WHERE c.num_conta IS NULL;  -- transações sem conta
```

---

## 10. PLANO DE ORQUESTRAÇÃO (Fase 16)

### 10.1 Apache Hop (Projeto 3 — ETL batch)

```
Workflows:
├── w01_carga_bronze.hwf        ← Ingestão diária de todos os CSVs
├── w02_silver_core.hwf         ← Limpeza core banking
├── w03_silver_macro.hwf        ← Enriquecimento macro + geo
├── w04_gold_dims.hwf           ← Carga das dimensões
├── w05_gold_fatos.hwf          ← Carga dos fatos
└── w06_validacao.hwf           ← DQ checks pós-carga

Agendamento: diário 02:00
Dependências: w01 → w02,w03 (paralelo) → w04 → w05 → w06
```

### 10.2 Airflow (Projeto 5 — Orquestração avançada)

```python
# dag_banvic_pipeline.py
dag = DAG(
    dag_id="banvic_daily_pipeline",
    schedule_interval="0 2 * * *",  # 02:00 diário
    catchup=False,
)

ingest_bronze >> [clean_silver_core, clean_silver_macro] >> load_dims >> load_fatos >> run_dq
```

### 10.3 n8n (Projeto 8 — Eventos e alertas)

```
Triggers:
├── Webhook: nova transação > R$ 50.000 → alerta Slack
├── Cron 08:00: fetch PTAX + Selic → update dim_tempo
├── Cron 1º do mês: fetch IPCA → update histórico
└── Webhook fraude detectada → notificação email CEO
```

### 10.4 Microsoft Fabric (Projeto 9)

```
Pipelines:
├── PL_Bronze_Ingest       ← Data Factory pipeline
├── PL_Silver_Transform    ← Dataflow Gen2
├── PL_Gold_Load          ← Spark Notebook
└── PL_PowerBI_Refresh    ← Semantic model refresh
```

---

## 11. DASHBOARD EXECUTIVO — ESPECIFICAÇÃO (Fase 17)

### 11.1 Estrutura do relatório Power BI

```
BanVic 360° — Dashboard Executivo
│
├── 1. Visão Geral (página inicial)
│   ├── KPI Card: Clientes ativos
│   ├── KPI Card: Volume total transações
│   ├── KPI Card: Patrimônio sob gestão
│   ├── KPI Card: Taxa de inadimplência
│   ├── KPI Card: Receita total do período
│   └── Mapa: Distribuição de agências por UF
│
├── 2. Agências
│   ├── Tabela: Ranking por saldo gerido
│   ├── Gráfico: Performance vs meta
│   ├── Mapa: Heatmap de clientes por cidade
│   └── Linha: Evolução de abertura de agências
│
├── 3. Crédito
│   ├── Funil: Propostas por status
│   ├── Scatter: Score vs taxa de aprovação
│   ├── Linha: NPL mensal
│   └── Tabela: Top 10 produtos de crédito
│
├── 4. Investimentos
│   ├── Donut: Mix de produtos (CDB, LCI, Fundos…)
│   ├── Linha: Evolução do patrimônio
│   ├── KPI: Rentabilidade média vs CDI
│   └── Tabela: Clientes com maior patrimônio
│
├── 5. Seguros
│   ├── KPI Card: Conversão por produto
│   ├── Linha: Prêmio mensal × sinistros
│   └── Tabela: Cross-sell rate por perfil
│
├── 6. Fraudes
│   ├── KPI: Taxa de fraude (%)
│   ├── Mapa: Fraudes por cidade
│   ├── Linha: Tentativas vs confirmadas
│   └── Barra: Canal com mais fraudes
│
├── 7. Economia
│   ├── Linha dupla: Selic × IPCA (12 meses)
│   ├── Linha: PTAX histórico
│   ├── Correlação: Volume tx × Selic
│   └── KPI: Custo de funding vs receita
│
└── 8. Análises Avançadas
    ├── Scatter: Clientes/pop × PIB per capita
    ├── Linha: Inadimplência × desemprego
    ├── Mapa: Market share por município
    └── Linha: Impacto clima × volume Pix
```

---

## 12. ANÁLISES AVANÇADAS (Fase 18)

### 12.1 Análises de correlação planejadas

| Análise | Métrica X | Métrica Y | Visualização |
|---|---|---|---|
| Crédito vs PIB | PIB per capita municipal | Taxa de aprovação de crédito | Scatter + regressão |
| Inadimplência vs desemprego | Taxa desemprego regional | NPL por UF | Scatter por trimestre |
| Receita vs Selic | Taxa Selic | Spread bancário | Linha dupla eixo Y |
| Fraudes vs horário | Hora do dia | Volume de fraudes | Heatmap hora×dia semana |
| Clima vs Pix | Temperatura / Chuva | Volume Pix diário | Scatter + sazonalidade |
| Penetração vs pop | Pop municipal | Clientes BanVic | Bubble chart por região |
| ROI agência nova | Custo abertura | Receita em 12 meses | Waterfall por agência |
| Produtividade colabor. | Tempo de empresa | Volume de negócios fechados | Scatter + quartis |

### 12.2 Queries de negócio (SQL showcases)

**Crescimento de clientes vs população IBGE:**
```sql
SELECT
    dm.regiao,
    dm.uf,
    dm.municipio,
    dm.populacao,
    COUNT(DISTINCT dc.sk_cliente) AS clientes_banvic,
    ROUND(COUNT(DISTINCT dc.sk_cliente) * 100.0 / dm.populacao, 4) AS penetracao_pct,
    dm.pib_per_capita
FROM gold.dim_municipio dm
LEFT JOIN gold.dim_cliente dc ON dc.sk_municipio = dm.sk_municipio
GROUP BY dm.sk_municipio, dm.regiao, dm.uf, dm.municipio, dm.populacao, dm.pib_per_capita
ORDER BY penetracao_pct DESC;
```

**Receita vs Selic (spread bancário):**
```sql
SELECT
    dt.ano,
    dt.mes,
    AVG(dt.taxa_selic) AS selic_media,
    SUM(fr.valor_receita) FILTER (WHERE fr.tipo_receita = 'Juros') AS receita_juros,
    SUM(fr.valor_receita) AS receita_total,
    ROUND(SUM(fr.valor_receita) FILTER (WHERE fr.tipo_receita = 'Juros')
        / NULLIF(SUM(ft.valor_transacao) FILTER (WHERE ft.flag_credito = FALSE), 0) * 100, 2)
    AS spread_pct
FROM gold.fato_receitas fr
JOIN gold.dim_tempo dt ON dt.sk_tempo = fr.sk_tempo
JOIN gold.fato_transacoes ft ON ft.sk_tempo = fr.sk_tempo
GROUP BY dt.ano, dt.mes, dt.taxa_selic
ORDER BY dt.ano, dt.mes;
```

---

## 13. CASOS DE USO POR STACK (Entrega Final)

| Stack | Projeto | Caso de uso principal | KPI demonstrado |
|---|---|---|---|
| **SQL Puro** | Projeto 1 | Star schema completo em PostgreSQL | Todos os 8 KPIs |
| **Python + PostgreSQL** | Projeto 2 | ETL com Pandas + psycopg2 + SQLAlchemy | KPIs + limpeza DQ |
| **Apache Hop** | Projeto 3 | Pipeline visual Bronze→Gold + Hop Server | KPIs + orquestração |
| **Docker** | Projeto 4 | Ambiente reproduzível (PostgreSQL + Hop + pgAdmin) | Infraestrutura |
| **Airflow** | Projeto 5 | DAGs incrementais + alertas + SLA | KPIs + monitoramento |
| **dbt** | Projeto 6 | Modelos SQL versionados + testes + docs | KPIs + lineage |
| **Databricks** | Projeto 7 | Delta Lake + Spark ML (score de crédito) | KPIs + ML |
| **n8n** | Projeto 8 | Webhooks + automação de alertas + API REST | KPIs + eventos |
| **Fabric** | Projeto 9 | One Lake + Power BI Embedded + Copilot | KPIs + BI executivo |

---

## 14. ROADMAP DE IMPLEMENTAÇÃO

```
FASE 0 — Fundação (próximo)
  ├── Validar 8 KPIs no gabarito (SQL manual)
  ├── Criar schema Bronze no PostgreSQL
  ├── Carregar todos os CSVs existentes
  └── Validar integridade referencial

FASE 1 — Completar datasets externos
  ├── Adicionar CDI, IGP-M, desemprego
  ├── Adicionar clima (Open-Meteo)
  ├── Adicionar renda/escolaridade por município
  └── Historizar: projetar 2025-2026 onde falta

FASE 2 — Geração sintética
  ├── Criar scripts/gerar_dados_sinteticos.py
  ├── Gerar 50k clientes
  ├── Gerar 3M+ transações
  └── Gerar fatos de investimentos, cartões, seguros

FASE 3 — Modelo dimensional completo
  ├── Criar todas as dims e fatos no Gold
  ├── Implementar SCD2 em dim_cliente
  └── Criar todas as views analíticas

FASE 4 — Projeto 1 (SQL Puro)
  ├── Star schema em PostgreSQL
  ├── 8 KPIs validados
  └── README completo

... (continuar para cada projeto)
```

---

*Documento gerado em 2026-06-03. Atualizar a cada fase concluída.*  
*Ver CLAUDE.md na raiz para estado atual e próximos passos.*
