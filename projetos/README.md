# Os 9 Projetos — BanVic 360

Este portfólio resolve **o mesmo problema bancário 9 vezes**, cada vez com uma ferramenta diferente.

O problema: pegar dados brutos de um banco (clientes, contas, transações) e transformá-los em 8 respostas de negócio — sempre chegando nos mesmos números.

---

## Por onde começar?

Se você não conhece nenhuma dessas ferramentas, esta é a ordem recomendada:

```
Projeto 1 → Projeto 4 → Projeto 2 → Projeto 5 → Projeto 6 → Projeto 3 → Projeto 7 → Projeto 8 → Projeto 9
  (SQL)      (Docker)   (Python)   (Airflow)    (dbt)       (Hop)     (Databricks)  (n8n)    (Fabric)
```

Se você já tem experiência, pode ir direto para o projeto que usar a ferramenta que você quer aprender.

---

## Configuração inicial (para todos os projetos)

Todos os projetos (exceto 7 e 9) precisam que você faça isso primeiro:

```bash
# 1. Instalar as dependências Python
pip install -r requirements.txt

# 2. Copiar o arquivo de configuração
cp .env.example .env

# 3. Subir o banco de dados
docker compose up -d

# 4. Carregar os dados e montar o pipeline completo
python scripts/entrypoint.py
```

O comando `python scripts/entrypoint.py` demora cerca de 5 minutos e faz tudo:
- Cria as tabelas Bronze e carrega os CSVs
- Transforma Bronze → Silver
- Monta o modelo Gold
- Valida as 8 KPIs contra o gabarito

Depois disso, cada projeto tem seu próprio comando para rodar. Os detalhes estão no README de cada pasta.

---

## Os 9 Projetos

| # | Pasta | Ferramenta | Pergunta central | Status |
|---|---|---|---|---|
| 1 | [01-sql-puro/](01-sql-puro/) | SQL + PostgreSQL | Até onde SQL puro consegue ir? | ✅ 7/7 KPIs |
| 2 | [02-python-postgresql/](02-python-postgresql/) | Python + pandas | Quando Python faz melhor que SQL? | ✅ 7/7 KPIs |
| 3 | [03-apache-hop/](03-apache-hop/) | Apache Hop | Quando arrastar blocos é melhor que código? | ✅ 7/7 KPIs |
| 4 | [04-docker/](04-docker/) | Docker | Como garantir que funciona em qualquer máquina? | ✅ Base de todos |
| 5 | [05-airflow/](05-airflow/) | Apache Airflow | Como fazer o pipeline rodar sozinho todo dia? | ✅ 7/7 KPIs |
| 6 | [06-dbt/](06-dbt/) | dbt | Como organizar transformações SQL em equipe? | ✅ 17 models |
| 7 | [07-databricks/](07-databricks/) | Databricks + PySpark | O que muda quando os dados não cabem numa máquina? | ✅ 8/8 KPIs |
| 8 | [08-n8n/](08-n8n/) | n8n | Quando automatizar sem escrever código? | ⏳ Estrutura criada |
| 9 | [09-fabric/](09-fabric/) | Microsoft Fabric + Power BI | Como entregar dados direto no dashboard do gestor? | ⏳ Em breve |

---

## O que cada projeto precisa

| Projeto | Precisa de Docker? | Precisa de nuvem? | Roda no Windows? |
|---|---|---|---|
| 1 — SQL Puro | Sim (banco local) | Não | Sim |
| 2 — Python | Sim (banco local) | Não | Sim |
| 3 — Apache Hop | Sim (Hop + banco) | Não | Sim |
| 4 — Docker | Sim | Não | Sim |
| 5 — Airflow | Sim (Airflow + banco) | Não | Sim |
| 6 — dbt | Sim (banco local) | Não | Sim |
| 7 — Databricks | Não | Sim (Databricks Community — gratuito) | Sim |
| 8 — n8n | Sim (n8n + banco) | Não | Sim |
| 9 — Fabric | Não | Sim (Microsoft Fabric) | Sim |

---

## Comparativo rápido

| Ferramenta | Custo | Curva de aprendizado | Quem usa no mercado |
|---|---|---|---|
| SQL + PostgreSQL | Gratuito | Baixa (todo mundo sabe SQL) | Todo lugar |
| Python + pandas | Gratuito | Média | Startups, ciência de dados |
| Apache Hop | Gratuito | Baixa | Empresas sem devs |
| Docker | Gratuito | Média | Times de engenharia |
| Airflow | Gratuito/pago | Alta | Grandes empresas |
| dbt | Gratuito (Core) | Média | Modern data stack |
| Databricks | Pago | Alta | Big tech, bancos |
| n8n | Gratuito (self-hosted) | Baixa | Times mistos |
| Fabric + Power BI | Pago por usuário | Média | Organizações Microsoft |

---

## A regra de ouro

Todos os 9 projetos produzem os mesmos 8 números:

| KPI | Resposta esperada |
|---|---|
| 1 — Saldo total | R$ 26.509.620,12 |
| 2 — Volume de transações | R$ 58.122.708,67 |
| 4 — Propostas enviadas | 525 |
| 4 — Propostas aprovadas | 513 |

Se o seu projeto chegou nesses números: está correto.
Se chegou em um número diferente: tem um bug para encontrar.

---

## Problemas comuns antes de rodar qualquer projeto

**"O banco não conecta"**
```bash
docker ps   # verifica se o container banvic-base-postgres está rodando
docker compose up -d   # sobe se não estiver
```

**"Tabelas não existem"**
```bash
python scripts/entrypoint.py   # recria tudo do zero
```

**"Erro de permissão no Windows"**
```bash
# Abrir o terminal como Administrador
# ou usar o Docker Desktop com WSL2 habilitado
```

**"Não tenho os dados CSV"**
Baixar do Drive: https://drive.google.com/drive/folders/1mtIBYJss1RqkfT_trxrcH5nanoiBHiuq?usp=sharing
