# BanVic 360° — Catálogo de Dados

> **Versão:** 1.1 | **Data:** 2026-06-10  
> **Escopo externo:** 14 datasets coletados + 5 séries projetadas

---

## Índice

1. [Dados Internos BanVic (Bronze/Raw)](#1-dados-internos-banvic)
2. [Dados Externos — Macroeconomia](#2-macroeconomia)
3. [Dados Externos — Calendário](#3-calendário)
4. [Dados Externos — Geografia](#4-geografia)
5. [Dados Externos — Status e limitações](#5-datasets-externos-status-e-limitações)
6. [Gold Layer — Dimensões](#6-dimensões-gold)
7. [Gold Layer — Fatos](#7-fatos-gold)
8. [Lineage (Data Lineage)](#8-lineage)

---

## 1. Dados Internos BanVic

### clientes
**Caminho:** `data/banvic/clientes.csv`  
**Linhas:** 998 | **Período:** 2010–2023

| Campo | Tipo | Nulo | Descrição | Problemas |
|---|---|---|---|---|
| `cod_cliente` | INTEGER | NÃO | Identificador único do cliente | OK |
| `primeiro_nome` | TEXT | NÃO | Primeiro nome | OK |
| `ultimo_nome` | TEXT | NÃO | Sobrenome | OK |
| `email` | TEXT | SIM | Email de contato | Pode estar desatualizado |
| `tipo_cliente` | TEXT | NÃO | PF ou PJ | Só PF na base atual |
| `data_inclusao` | TIMESTAMP | NÃO | Data de cadastro | Timezone UTC inconsistente |
| `cpfcnpj` | TEXT | SIM | CPF no formato XXX.XXX.XXX-XX | Alguns sem máscara |
| `data_nascimento` | DATE | SIM | Data de nascimento | Alguns com datas inconsistentes |
| `endereco` | TEXT | SIM | Endereço completo em campo único | Precisa parse |
| `cep` | TEXT | SIM | CEP do endereço | Formato inconsistente |

**Campos derivados (Silver):** `cidade`, `uf`, `logradouro`, `idade`, `faixa_etaria`

---

### contas
**Caminho:** `data/banvic/contas.csv`  
**Linhas:** 999 | **Período:** 2011–2023

| Campo | Tipo | Nulo | Descrição | Problemas |
|---|---|---|---|---|
| `num_conta` | INTEGER | NÃO | Número único da conta | OK |
| `cod_cliente` | INTEGER | NÃO | FK → clientes | OK |
| `cod_agencia` | INTEGER | NÃO | FK → agencias | OK |
| `cod_colaborador` | INTEGER | NÃO | FK → colaboradores | OK |
| `tipo_conta` | TEXT | NÃO | PF ou PJ (mesmo que cliente) | Deveria ser produto (corrente, poupança) |
| `data_abertura` | TIMESTAMP | NÃO | Data de abertura da conta | Timezone UTC |
| `saldo_total` | FLOAT | NÃO | Saldo total em R$ | Float ruidoso (ex: 2984.7614999) |
| `saldo_disponivel` | FLOAT | NÃO | Saldo disponível em R$ | Float ruidoso |
| `data_ultimo_lancamento` | TIMESTAMP | SIM | Data da última transação | Timezone UTC |

**Campos derivados (Silver):** `produto_conta`, `flag_ativa`, `saldo_arredondado`

---

### agencias
**Caminho:** `data/banvic/agencias.csv`  
**Linhas:** 10

| Campo | Tipo | Nulo | Descrição | Problemas |
|---|---|---|---|---|
| `cod_agencia` | INTEGER | NÃO | Código único da agência | OK |
| `nome` | TEXT | NÃO | Nome da agência | Encoding quebrado |
| `endereco` | TEXT | SIM | Endereço completo | OK |
| `cidade` | TEXT | NÃO | Cidade | OK |
| `uf` | CHAR(2) | NÃO | UF da agência | OK |
| `data_abertura` | DATE | NÃO | Data de abertura | OK |
| `tipo_agencia` | TEXT | NÃO | Física ou Digital | OK |

**Campos a adicionar (Silver/expansão):** `regiao`, `codigo_ibge`, `lat`, `lon`, `meta_comercial`

---

### colaboradores
**Caminho:** `data/banvic/colaboradores.csv`  
**Linhas:** 100

| Campo | Tipo | Nulo | Descrição |
|---|---|---|---|
| `cod_colaborador` | INTEGER | NÃO | Código único |
| `primeiro_nome` | TEXT | NÃO | Primeiro nome |
| `ultimo_nome` | TEXT | NÃO | Sobrenome |
| `email` | TEXT | SIM | Email corporativo |
| `cpf` | TEXT | SIM | CPF no formato XXX.XXX.XXX-XX |
| `data_nascimento` | DATE | SIM | Data de nascimento |
| `endereco` | TEXT | SIM | Endereço completo |
| `cep` | TEXT | SIM | CEP |

**Campos a adicionar (expansão):** `cargo`, `departamento`, `salario`, `data_admissao`

---

### colaborador_agencia
**Caminho:** `data/banvic/colaborador_agencia.csv`  
**Linhas:** 100

| Campo | Tipo | Nulo | Descrição |
|---|---|---|---|
| `cod_colaborador` | INTEGER | NÃO | FK → colaboradores |
| `cod_agencia` | INTEGER | NÃO | FK → agencias |

**Campos a adicionar:** `data_inicio`, `data_fim`, `cargo_na_agencia`

---

### transacoes
**Caminho:** `data/banvic/transacoes.csv`  
**Linhas:** 71.999 | **Período:** 2010–2023

| Campo | Tipo | Nulo | Descrição | Problemas |
|---|---|---|---|---|
| `cod_transacao` | INTEGER | NÃO | Código único da transação | OK |
| `num_conta` | INTEGER | NÃO | FK → contas | OK |
| `data_transacao` | TIMESTAMP | NÃO | Data e hora da transação | Timezone UTC |
| `nome_transacao` | TEXT | NÃO | Tipo da transação | Canal embutido no nome |
| `valor_transacao` | INTEGER/FLOAT | NÃO | Valor (negativo=débito) | OK |

**Tipos existentes:** Pix-Realizado, Pix-Recebido, TED-Realizado, TED-Recebido, DOC-Realizado, DOC-Recebido, Compra Crédito, Compra Débito, Saque, Pix Saque, Depósito em espécie, Pagamento de boleto, Estorno de Débito, Transferência entre CC (Débito/Crédito)

---

### propostas_credito
**Caminho:** `data/banvic/propostas_credito.csv`  
**Linhas:** 2.000 | **Período:** 2014–2023

| Campo | Tipo | Nulo | Descrição | Problemas |
|---|---|---|---|---|
| `cod_proposta` | INTEGER | NÃO | Código único | OK |
| `cod_cliente` | INTEGER | NÃO | FK → clientes | OK |
| `cod_colaborador` | INTEGER | NÃO | FK → colaboradores | OK |
| `data_entrada_proposta` | TIMESTAMP | NÃO | Data de entrada | Timezone UTC |
| `taxa_juros_mensal` | FLOAT | NÃO | Taxa mensal em decimal (0.0194 = 1,94%) | OK |
| `valor_proposta` | FLOAT | NÃO | Valor total solicitado | Float ruidoso |
| `valor_financiamento` | FLOAT | NÃO | Valor a financiar | OK |
| `valor_entrada` | FLOAT | NÃO | Valor de entrada | Float ruidoso |
| `valor_prestacao` | FLOAT | NÃO | Valor da parcela | Float ruidoso |
| `quantidade_parcelas` | INTEGER | NÃO | Número de parcelas | OK |
| `carencia` | INTEGER | NÃO | Meses de carência | OK |
| `status_proposta` | TEXT | NÃO | Status atual | Sem 'Reprovada'; sem data de decisão |

**Status existentes:** Enviada (527), Aprovada (514), Em análise (468), Validação documentos (491)

---

## 2. Macroeconomia

### ipca.csv
**Caminho:** `external_data/macroeconomia/ipca.csv`  
**Linhas:** 192 | **Período:** 2010-01 a 2025-12 | **Fonte:** BCB SGS

| Campo | Tipo | Descrição |
|---|---|---|
| `data` | DATE | Primeiro dia do mês de referência |
| `ano` | SMALLINT | Ano |
| `mes` | CHAR(3) | Mês abreviado em PT (JAN-DEZ) |
| `mes_num` | SMALLINT | Número do mês (1-12) |
| `indice` | NUMERIC | Índice acumulado (base: jan/2010=3040,22) |
| `no_mes` | NUMERIC | Variação % no mês |
| `acumulado_3m` | NUMERIC | Variação % nos últimos 3 meses |
| `acumulado_12m` | NUMERIC | Variação % nos últimos 12 meses |
| `acumulado_ano` | NUMERIC | Variação % no ano corrente |

### selic.csv
**Caminho:** `external_data/macroeconomia/selic.csv`  
**Linhas:** 1.255 | **Período:** 2020-01-02 a 2024-12-31 | **Fonte:** BCB SGS-11

| Campo | Tipo | Descrição |
|---|---|---|
| `data` | DATE | Data de referência |
| `taxa_selic` | NUMERIC | Taxa Selic efetiva (% a.a., base 252) |

### dolar_ptax.csv
**Caminho:** `external_data/macroeconomia/dolar_ptax.csv`  
**Linhas:** 1.255 | **Período:** 2020-01-02 a 2024-12-31 | **Fonte:** BCB PTAX API

| Campo | Tipo | Descrição |
|---|---|---|
| `data` | DATE | Data do pregão |
| `cotacao_compra` | NUMERIC | Cotação de compra (R$/USD) |
| `cotacao_venda` | NUMERIC | Cotação de venda (R$/USD) |
| `cotacao_media` | NUMERIC | Média de compra e venda |

---

## 3. Calendário

### feriados.csv
**Caminho:** `external_data/calendario/feriados.csv`  
**Linhas:** 74 | **Período:** 2020–2025 | **Fonte:** BrasilAPI

| Campo | Tipo | Descrição |
|---|---|---|
| `data` | DATE | Data do feriado |
| `nome_feriado` | VARCHAR | Nome oficial |
| `tipo` | VARCHAR | national / bank / optional |

---

## 4. Geografia

### municipios.csv
**Caminho:** `external_data/geografia/municipios.csv`  
**Linhas:** 5.571 | **Fonte:** IBGE API v1

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo_ibge` | INTEGER | Código IBGE (7 dígitos) |
| `municipio` | VARCHAR | Nome do município |
| `uf` | CHAR(2) | Sigla da UF |
| `uf_nome` | VARCHAR | Nome completo da UF |
| `regiao` | VARCHAR | Norte / Nordeste / Centro-Oeste / Sudeste / Sul |
| `regiao_sigla` | CHAR(2) | N / NE / CO / SE / S |

### populacao.csv
**Caminho:** `external_data/geografia/populacao.csv`  
**Linhas:** 5.570 | **Fonte:** IBGE Censo 2022 (Tabela 9606)

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo_ibge` | INTEGER | Código IBGE do município |
| `municipio` | VARCHAR | Nome do município + UF |
| `ano` | SMALLINT | Ano de referência (2022) |
| `populacao` | INTEGER | Total de residentes |

### pib_municipal.csv
**Caminho:** `external_data/geografia/pib_municipal.csv`  
**Linhas:** 5.570 | **Fonte:** IBGE Tabela 5938 (2021)

| Campo | Tipo | Descrição |
|---|---|---|
| `codigo_ibge` | INTEGER | Código IBGE do município |
| `municipio` | VARCHAR | Nome do município + UF |
| `ano` | SMALLINT | Ano de referência (2021) |
| `pib_total` | BIGINT | PIB total em R$ |
| `pib_per_capita` | NUMERIC | PIB per capita calculado (R$) |

---

## 5. Datasets Externos: Status e Limitações

| Dataset | Arquivo | Status |
|---|---|---|
| CDI diário | `macroeconomia/cdi.csv` | Coletado |
| IGP-M mensal | `macroeconomia/igpm.csv` | Coletado |
| Taxa de desemprego | `macroeconomia/desemprego.csv` | Coletado pela série BCB SGS-24369 |
| Euro PTAX | `macroeconomia/euro_ptax.csv` | Coletado |
| Renda municipal | `geografia/renda_municipal.csv` | Proxy estimada por PIB per capita / 12 |
| Escolaridade municipal | `geografia/escolaridade_municipal.csv` | Placeholder; não usar como dado observado |
| Clima histórico | `clima/clima_historico.csv` | Parcial: 91 de 99 cidades por rate limit |

Para baixar novamente:
```bash
python scripts/download_datasets.py
```

---

## 6. Dimensões Gold

| Tabela | Linhas de referência | Tipo SCD | Chave Natural |
|---|---|---|---|
| `gold.dim_tempo` | 2.557 (2020–2026) | SCD1 | `data` |
| `gold.dim_cliente` | 50.000+ | SCD2 | `cod_cliente` |
| `gold.dim_agencia` | 100 | SCD1 | `cod_agencia` |
| `gold.dim_colaborador` | 1.200 | SCD1 | `cod_colaborador` |
| `gold.dim_municipio` | 5.571 | SCD1 | `codigo_ibge` |
| `gold.dim_produto` | 28 | SCD1 | `cod_produto` |
| `gold.dim_canal` | 12 | SCD1 | `nome_canal` |
| `gold.dim_score_credito` | 5 | Estática | `faixa_score` |

---

## 7. Fatos Gold

| Tabela | Grão | Linhas de referência | Partição |
|---|---|---|---|
| `gold.fato_transacoes` | 1 por transação | 2.642.400 | ano+mes |
| `gold.fato_contas` | 1 por conta, snapshot corrente | 70.121 | não aplicável |
| `gold.fato_propostas_credito` | 1 por proposta | 56.635 | ano |
| `gold.fato_investimentos` | 1 por posição | 16.008 | ano |
| `gold.fato_cartoes` | 1 por fatura mensal | 537.694 | ano+mes |
| `gold.fato_seguros` | 1 por apólice | 17.769 | ano |
| `gold.fato_inadimplencia` | 1 por contrato inadimplente | 468 | bucket |
| `gold.fato_receitas` | 1 por tipo+agência+mês | derivada na Gold | ano+mes |
| `gold.fato_fraudes` | 1 por ocorrência | 1.400 | ano |

---

## 8. Lineage (Data Lineage)

```
FONTES                    BRONZE           SILVER              GOLD
──────                    ──────           ──────              ────

clientes.csv          ──▶ bronze_cli   ──▶ silver_cli     ──▶ dim_cliente
contas.csv            ──▶ bronze_con   ──▶ silver_con     ──▶ fato_contas
                                                         ──▶ dim_produto (tipo conta)
transacoes.csv        ──▶ bronze_tx    ──▶ silver_tx      ──▶ fato_transacoes
agencias.csv          ──▶ bronze_ag    ──▶ silver_ag      ──▶ dim_agencia
colaboradores.csv     ──▶ bronze_col   ──▶ silver_col     ──▶ dim_colaborador
colabor_agencia.csv   ──▶ bronze_ca    ──▶ (merge)        ──▶ dim_colaborador.sk_agencia
propostas.csv         ──▶ bronze_prop  ──▶ silver_prop    ──▶ fato_propostas_credito

ipca.csv              ──▶ bronze_ipca  ──▶ silver_macro   ──▶ dim_tempo.indice_ipca
selic.csv             ──▶ bronze_selic ──▶ silver_macro   ──▶ dim_tempo.taxa_selic
dolar_ptax.csv        ──▶ bronze_ptax  ──▶ silver_macro   ──▶ dim_tempo.cotacao_dolar
feriados.csv          ──▶ bronze_fer   ──▶ (merge)        ──▶ dim_tempo.eh_feriado
municipios.csv        ──▶ bronze_mun   ──┐
populacao.csv         ──▶ bronze_pop   ──┼▶ silver_mun    ──▶ dim_municipio
pib_municipal.csv     ──▶ bronze_pib   ──┘

dim_cliente ──────────────────────────────────────────────────▶ fato_transacoes
dim_agencia ──────────────────────────────────────────────────▶ fato_transacoes
dim_municipio ────────────────────────────────────────────────▶ dim_cliente.sk_municipio
                                                               ▶ dim_agencia.sk_municipio

(Sintéticos — Fase 7)
gerar_dados_sinteticos.py ──▶ clientes_sinteticos.csv ──▶ bronze_cli (append)
                          ──▶ transacoes_sinteticas.csv ──▶ bronze_tx (append)
                          ──▶ investimentos.csv ──▶ bronze_inv
                          ──▶ cartoes.csv ──▶ bronze_cart
                          ──▶ seguros.csv ──▶ bronze_seg
```

---

*Catálogo revisado manualmente em 2026-06-10. A atualização automática ainda não foi implementada.*
