# Projeto 2 — Python + PostgreSQL

Este projeto faz o mesmo pipeline do Projeto 1, mas em vez de escrever SQL direto no banco, escreve código Python que se conecta ao PostgreSQL e executa as transformações.

**Pergunta principal:** _Quando Python faz melhor do que SQL puro?_

---

## O que muda em relação ao Projeto 1

No Projeto 1, as regras de transformação ficam dentro do banco, em arquivos `.sql`.
Neste projeto, elas ficam em código Python — usando **pandas** para manipular os dados e **SQLAlchemy** para conversar com o banco.

**O que é pandas?** É uma biblioteca Python que trata dados como uma planilha: você pode filtrar linhas, criar colunas, juntar tabelas — mas no código, não no banco.

**O que é SQLAlchemy?** É a "ponte" entre Python e o banco de dados. Em vez de rodar `psql`, você escreve `engine.connect()` e os dados vão e voltam pelo Python.

O resultado final é o mesmo: os mesmos dados no mesmo modelo, as mesmas 8 respostas corretas.

---

## Resultado

```
7/7 KPIs corretos — APROVADO
```

---

## Arquivos do projeto

```
projetos/02-python-postgresql/
├── etl/
│   ├── conexao.py       Como se conectar ao banco (lê o .env automaticamente)
│   ├── silver.py        10 transformações Bronze → Silver em pandas
│   ├── gold_dims.py     Carga das 6 dimensões Gold
│   ├── gold_fatos.py    Carga das 3 tabelas fato
│   └── pipeline.py      Orquestrador — chama cada etapa na ordem certa
├── notebooks/
│   └── 01_pipeline_banvic.ipynb  Versão interativa com gráficos
└── run.py               Ponto de entrada: python run.py
```

---

## Como executar

### Pré-requisitos

O banco precisa estar rodando com os dados Bronze carregados:

```bash
# Na raiz do projeto
pip install -r requirements.txt
docker compose up -d
python scripts/entrypoint.py   # carrega Bronze e cria os schemas
```

### Pipeline completo

```bash
python projetos/02-python-postgresql/run.py
```

**O que você vai ver na tela:**
```
=======================================================
BanVic 360 -- Projeto 2: Python + PostgreSQL
=======================================================

[1/3] Transformando Silver (pandas)...
[silver] concluido em 12.3s

[2/3] Populando Gold Dims (pandas + SQLAlchemy)...
[gold_dims] concluido em 3.1s

[3/3] Populando Gold Fatos (pandas + merge)...
[gold_fatos] concluido em 8.7s

Pipeline completo em 24.1s
Execute 'python scripts/validar_gabarito_pg.py' para validar os KPIs.
=======================================================
```

### Por etapa (útil para testar só uma parte)

```bash
# Só Silver
python projetos/02-python-postgresql/run.py --etapa silver

# Silver + dimensões Gold
python projetos/02-python-postgresql/run.py --etapa silver gold_dims

# Só os fatos Gold (Silver e dimensões já criados)
python projetos/02-python-postgresql/run.py --etapa gold_fatos
```

### Verificar as respostas

```bash
python scripts/validar_gabarito_pg.py
```

### Notebook interativo (opcional)

Se quiser ver gráficos e explorar os dados passo a passo:

```bash
pip install jupyter matplotlib
jupyter notebook projetos/02-python-postgresql/notebooks/01_pipeline_banvic.ipynb
```

---

## O que o Python faz que SQL não faz fácil

Abaixo, um exemplo real do `silver.py`. Em SQL isso seria uma query complexa; em Python é linha a linha, fácil de debugar:

```python
# Lê os clientes do Bronze
df = pd.read_sql("SELECT * FROM bronze_clientes", engine)

# Remove duplicatas (mantém o mais recente)
df = df.drop_duplicates(subset=["cod_cliente"], keep="last")

# Converte a data de nascimento para o tipo correto
df["data_nascimento"] = pd.to_datetime(df["data_nascimento"])

# Calcula a faixa etária (impossível fazer isso em 1 linha de SQL)
df["faixa_etaria"] = pd.cut(
    df["idade"],
    bins=[0, 24, 34, 44, 54, 64, 999],
    labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
)

# Salva de volta no banco, na tabela Silver
df.to_sql("clientes_clean", engine, schema="silver", if_exists="replace")
```

Cada passo você pode inspecionar com `df.head()` ou `print(df.shape)` — sem precisar abrir o pgAdmin.

---

## Se algo não funcionar

**"ModuleNotFoundError: No module named 'pandas'"**
```bash
pip install -r requirements.txt
```

**"could not connect to server" (banco não conecta)**
```bash
docker ps   # verifique se banvic_postgres está rodando
docker compose up -d
```

**"relation bronze_clientes does not exist" (Bronze não carregado)**
```bash
python scripts/entrypoint.py   # recria tudo
```

**"UndefinedTable: silver.clientes_clean" ao rodar gold_dims sem silver**
```bash
python projetos/02-python-postgresql/run.py --etapa silver gold_dims gold_fatos
```

---

## SQL Puro vs Python — quando usar cada um

| O que você precisa | Melhor escolha |
|---|---|
| Velocidade bruta de processamento | SQL Puro |
| Testar partes do código separadamente | Python |
| Fazer debug (inspecionar dados no meio do caminho) | Python (`df.head()`, `df.info()`) |
| Usar Machine Learning junto com o pipeline | Python |
| Reutilizar lógica em lugares diferentes | Python (funções reutilizáveis) |
| Time que só sabe SQL | SQL Puro |
| Sem instalar dependências extras | SQL Puro |

---

## Quando usar Python + PostgreSQL

| Situação | Faz sentido? |
|---|---|
| Time de cientistas de dados ou engenheiros Python | Sim — sem precisar de SQL avançado |
| Regras de negócio complexas demais para SQL | Sim — código Python é mais testável |
| Integração com APIs externas ou modelos de ML | Sim — nativo em Python |
| Exploração de dados com gráficos | Sim — notebooks Jupyter |
| Pipeline com 100 milhões de linhas | Não — use Databricks (Projeto 7) |
| Time que prefere SQL e tem warehouse maduro | Não — SQL Puro ou dbt |
