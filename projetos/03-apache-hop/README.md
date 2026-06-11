# Projeto 3 — Apache Hop

Este projeto faz o mesmo pipeline do BanVic usando o **Apache Hop** — uma ferramenta visual de ETL onde você monta o pipeline arrastando blocos na tela, sem escrever código.

**Pergunta principal:** _Quando uma ferramenta visual faz mais sentido do que escrever código?_

---

## O que é o Apache Hop

Imagine montar um fluxo de dados como montar peças de LEGO: você pega blocos prontos (ler arquivo CSV, executar SQL, salvar no banco) e conecta um no outro. O Hop cuida de executar na ordem certa, tratando erros no meio do caminho.

É muito usado em empresas onde parte do time não é programador mas precisa entender e modificar o pipeline.

---

## Resultado

```
7/7 KPIs corretos — APROVADO
```

---

## Arquivos do projeto

```
projetos/03-apache-hop/
├── hop/
│   ├── project-config.json          Configuração do projeto no Hop
│   ├── metadata/rdbms/
│   │   └── banvic_pg.json           Configuração da conexão com o banco
│   ├── pipelines/
│   │   ├── 01_silver.hpl            Transforma Bronze → Silver (12 blocos)
│   │   ├── 02_gold_dims.hpl         Cria as dimensões Gold (8 blocos)
│   │   └── 03_gold_fatos.hpl        Cria os fatos Gold (5 blocos)
│   └── workflows/
│       └── 00_banvic_pipeline.hwf   Orquestra tudo + trata erros
├── docker-compose.yml               Hop 2.10 rodando em Docker
├── run.bat                          Execução no Windows
└── run.sh                           Execução no Linux/Mac
```

---

## Como executar

### Pré-requisitos

O banco precisa estar rodando com os dados Bronze carregados:

```bash
# Na raiz do projeto
docker compose up -d
python scripts/carga_bronze.py
```

### Rodar via Docker (recomendado)

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

### Ver o pipeline na interface visual

1. Baixe o Apache Hop em [hop.apache.org](https://hop.apache.org)
2. Abra o Hop GUI
3. Vá em **Arquivo → Novo Projeto** e aponte para `projetos/03-apache-hop/hop/`
4. Abra qualquer arquivo `.hpl` para ver o pipeline visualmente

### Verificar as respostas

```bash
python scripts/validar_gabarito_pg.py
```

---

## Como o pipeline funciona por dentro

Cada pipeline segue o mesmo padrão:

```
[Gera 1 linha] → [Executa SQL 1] → [Executa SQL 2] → ... → [Finaliza]
```

O bloco "Gera 1 linha" é o ponto de partida — ele dispara o fluxo.
Cada bloco "Executa SQL" roda uma instrução SQL no banco.
Se qualquer bloco falhar, o workflow para e registra o erro.

### Fluxo de controle (workflow)

```
Início
  ↓
Limpar tabelas (evitar dados duplicados)
  ↓ sucesso         ↓ erro
Silver             PARAR
  ↓ sucesso         ↓ erro
Gold Dimensões     PARAR
  ↓ sucesso         ↓ erro
Gold Fatos         PARAR
  ↓
Sucesso!
```

---

## Hop vs Código

| O que você precisa | Hop | Python/SQL |
|---|---|---|
| Ver o fluxo visualmente | Sim — arrastar e soltar | Não — precisa ler código |
| Modificar um passo | Clicar + editar | Editar arquivo de código |
| Debug (ver dados no meio) | Sim — preview de dados em cada bloco | `df.head()` ou logs |
| Rastreabilidade dos dados | Sim — nativo | Manual |
| Portabilidade entre bancos | Sim — troca a conexão | Depende do código |
| Curva de aprendizado | Baixa | Média a alta |
| Time sem programadores | Sim | Não |

---

## Quando usar Apache Hop

| Situação | Faz sentido? |
|---|---|
| Time sem perfil de programação | Sim — visual, intuitivo |
| Precisar de auditoria e rastreabilidade | Sim — nativo |
| Migrar dados entre bancos diferentes | Sim — abstrai a conexão |
| Transformações pesadas com Python/ML | Não — use Python puro |
| Pipeline simples em time que só sabe SQL | Não — SQL Puro ou dbt são mais diretos |
