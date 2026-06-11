# Projeto 2 — Python + PostgreSQL

Este projeto faz o mesmo pipeline do Projeto 1, mas em vez de escrever SQL direto no banco, escreve código Python que se conecta ao PostgreSQL e executa as transformações.

**Pergunta principal:** _Quando Python faz melhor do que SQL puro?_

---

## O que muda em relação ao Projeto 1

No Projeto 1, as regras de transformação ficam dentro do banco, em arquivos `.sql`.
Neste projeto, elas ficam em código Python — usando pandas para manipular os dados
e psycopg2 para conversar com o banco.

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
│   ├── conexao.py       Como se conectar ao banco (reutilizável)
│   ├── silver.py        10 transformações Bronze → Silver em pandas
│   ├── gold_dims.py     Carga das 6 dimensões Gold
│   ├── gold_fatos.py    Carga das 3 tabelas fato
│   └── pipeline.py      Orquestrador — chama cada etapa na ordem
├── notebooks/
│   └── 01_pipeline_banvic.ipynb  Exploração interativa com gráficos
└── run.py               Ponto de entrada: python run.py
```

---

## Como executar

Antes de começar, o banco precisa estar rodando com os dados carregados:

```bash
# Na raiz do projeto
docker compose up -d
python scripts/carga_bronze.py
```

### Pipeline completo

```bash
python projetos/02-python-postgresql/run.py
```

### Por etapa (útil para testar só uma parte)

```bash
# Só Silver
python projetos/02-python-postgresql/run.py --etapa silver

# Silver + Gold
python projetos/02-python-postgresql/run.py --etapa gold_dims gold_fatos
```

### Notebook interativo

```bash
pip install jupyter matplotlib
jupyter notebook projetos/02-python-postgresql/notebooks/01_pipeline_banvic.ipynb
```

### Verificar as respostas

```bash
python scripts/validar_gabarito_pg.py
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
