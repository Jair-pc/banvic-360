# Projeto 5 — Airflow + Python

Este projeto faz o mesmo pipeline do BanVic usando o **Apache Airflow** — uma ferramenta que agenda, executa e monitora pipelines de dados automaticamente.

**Pergunta principal:** _O que muda quando o pipeline precisa rodar todo dia, sozinho, e te avisar quando algo falha?_

---

## O problema que o Airflow resolve

Nos projetos anteriores, você roda os scripts manualmente. Mas em produção, ninguém vai abrir o terminal todo dia às 6h para digitar `python pipeline.py`.

O Airflow funciona como um **gerente de tarefas**: você define o que precisa ser feito, em que ordem, em que horário, e o que acontece se algo der errado. Ele cuida do resto.

---

## Resultado

```
7/7 KPIs corretos — APROVADO
```

---

## Prints

### Lista de DAGs — pipeline ativo (toggle azul)

![DAG list](prints/01_dag_list.png)

### Graph view — todas as tarefas com sucesso

![Graph success](prints/02_graph_success.png)

---

## Arquivos do projeto

```
projetos/05-airflow/
├── dags/
│   └── banvic_pipeline.py   O pipeline completo definido como DAG
├── docker-compose.yml       Airflow 2.9 rodando via Docker
├── run.bat                  Inicialização no Windows
└── run.sh                   Inicialização no Linux/Mac
```

---

## Como o pipeline está organizado (DAG)

No Airflow, um pipeline é chamado de **DAG** (Directed Acyclic Graph — grafo de tarefas com dependências). Cada caixinha é uma tarefa, as setas mostram a ordem.

```
[Verificar Bronze]          ← Para tudo se os dados não chegaram ainda
       |
[Preparar ambiente]         ← Limpa tabelas para recarregar sem duplicatas
       |
┌──────┴──────────────────────────────────────────────┐
│          Silver (7 tarefas em paralelo)              │
│ clientes  contas  transações  agências  colaboradores│
│           propostas  dados externos                  │
└──────────────────────────┬──────────────────────────┘
                           |
                      [Índices]
                           |
              ┌────────────┴────────────┐
              │        Gold             │
              │    Dimensões → Fatos    │
              └────────────┬────────────┘
                           |
                  [Validar KPIs]        ← Compara com o gabarito
```

As 7 tarefas Silver rodam ao mesmo tempo (em paralelo) porque não dependem umas das outras. Isso acelera o pipeline.

---

## Como executar

### Pré-requisitos

O banco precisa estar rodando com os dados Bronze carregados:

```bash
# Na raiz do projeto
docker compose up -d
python scripts/carga_bronze.py
```

### Subir o Airflow

**Windows:**
```bat
cd projetos\05-airflow
run.bat
```

**Linux/Mac:**
```bash
cd projetos/05-airflow
chmod +x run.sh && ./run.sh
```

**Primeira vez (manual):**
```bash
cd projetos/05-airflow
docker compose up airflow-init    # inicializa o banco de metadados do Airflow
docker compose up -d              # sobe o scheduler e o webserver
```

### Acessar a interface

Abra `http://localhost:8080` no navegador.
- Login: `admin`
- Senha: `admin`

Na interface:
1. Encontre a DAG `banvic_pipeline`
2. Ative o botão de play (está pausada por padrão para não rodar sozinha)
3. Clique em **Trigger DAG** para rodar agora

**O que você vai ver:**

Cada tarefa fica colorida em tempo real:
- Cinza = esperando
- Amarelo = rodando
- Verde = concluído com sucesso
- Vermelho = falhou

### Ver o resultado da validação

Na interface do Airflow: clique em `banvic_pipeline` → clique em `validar_kpis` → clique em **Logs**

Ou no terminal:
```bash
docker logs banvic-p05-scheduler | grep -i "aprovad\|falhou"
```

### Verificar as respostas no banco

```bash
python scripts/validar_gabarito_pg.py
```

### Parar o Airflow

```bash
docker compose down
```

---

## Se algo não funcionar

**Airflow demora para aparecer em localhost:8080**

É normal — o Airflow leva 1-2 minutos para iniciar completamente. Aguarde e recarregue a página.

**"DAG banvic_pipeline não aparece na lista"**
```bash
# Veja se o arquivo foi carregado corretamente
docker logs banvic-p05-scheduler | grep "banvic"
# Aguarde 30 segundos — o Airflow verifica novos DAGs periodicamente
```

**Tarefa Silver falhou (vermelho)**
```bash
# Clique na tarefa → Logs para ver o erro específico
# Geralmente é problema de conexão com o banco ou Bronze não carregado

# Verificar o banco:
docker ps   # banvic-base-postgres deve estar "healthy"
```

**"connection refused to banvic-base-postgres"**
```bash
# O Airflow usa a rede banvic_net — o banco precisa estar rodando
docker compose up -d   # na raiz do projeto
```

---

## O que o Airflow adiciona ao pipeline

| Preciso de | Scripts Python diretos | Airflow |
|---|---|---|
| Rodar todo dia no horário certo | Configurar cron manualmente | Nativo — `schedule="0 6 * * *"` |
| Tentar de novo se falhar | Programar manualmente | Nativo — `retries=2, retry_delay=3min` |
| Ver o status de cada passo | `print()` no terminal | Interface visual com histórico |
| Reexecutar só uma tarefa que falhou | Rodar o script inteiro de novo | Clicar na tarefa específica |
| Rodar várias tarefas ao mesmo tempo | `threading` (complicado) | Automático |
| Ver o histórico de execuções | Arquivo de log | Banco de metadados + interface |
| Receber alerta quando falhar | Implementar do zero | `email_on_failure=True` |

---

## Como a conexão com o banco funciona

A senha do banco não fica no código. Ela é passada como variável de ambiente no docker-compose:

```
AIRFLOW_CONN_BANVIC_PG=postgresql://banvic_user:banvic_pass@banvic-base-postgres:5432/banvic
```

O Airflow registra isso como uma "Connection" com o nome `banvic_pg`.
No código da DAG, basta usar `PostgresHook(postgres_conn_id="banvic_pg")` — sem nenhuma senha visível.

Em produção, essa variável viria de um cofre de senhas (AWS Secrets Manager, Vault, etc.). O código da DAG não muda.

---

## Quando usar Airflow

| Situação | Faz sentido? |
|---|---|
| Pipeline que roda todo dia com dependências entre etapas | Sim — feito para isso |
| Precisar de retry automático e alertas em falha | Sim — nativo |
| Time que precisa acompanhar o status visualmente | Sim — interface clara |
| Pipeline que roda uma vez só | Não — overhead desnecessário |
| Time sem perfil DevOps para manter o Airflow | Com cuidado — tem custo operacional |
