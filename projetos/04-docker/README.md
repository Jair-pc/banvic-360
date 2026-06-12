# Projeto 4 — Docker + Ambiente

Este projeto demonstra como criar um ambiente **completamente reproduzível** para o BanVic 360 — qualquer pessoa com Docker pode subir tudo com um único comando e chegar nos mesmos resultados.

**Pergunta principal:** _Como fazer o pipeline rodar igual no meu computador, no computador do colega e num servidor na nuvem?_

---

## Resultado

```
7/7 KPIs corretos — APROVADO (container isolado porta 5433)
Ambiente sobe do zero em ~5 minutos (inclui carga de 3.7M linhas)
```

---

## Arquivos do projeto

```
projetos/04-docker/
├── docker-compose.yml          Postgres 15 (5433) + pgAdmin (5051)
├── init/
│   └── 01_setup.sql            Schemas + extensoes (auto-executa no primeiro start)
├── pgadmin/
│   └── servers.json            Conexao pre-configurada no pgAdmin
├── setup.bat                   Setup completo no Windows
└── setup.sh                    Setup completo no Linux/Mac
```

---

## Como executar

### Pre-requisitos

- Docker Desktop rodando
- Python 3 com dependencias: `pip install -r ../../requirements.txt`
- Dados de origem no diretorio `data/` (ver README raiz)

### Windows

```bat
cd projetos\04-docker
setup.bat
```

### Linux / Mac

```bash
cd projetos/04-docker
chmod +x setup.sh && ./setup.sh
```

### O que o setup faz (passo a passo)

```
[1/6] docker compose up -d
      Sobe postgres:15 na porta 5433 e pgAdmin na porta 5051
      O init/01_setup.sql cria automaticamente os schemas bronze/silver/gold

[2/6] Aguarda banco ficar healthy (pg_isready)

[3/6] Cria DDL Bronze (35 tabelas)

[4/6] Carrega 3.7M linhas via Python COPY client-side (~3-5 min)

[5/6] Transforma Silver, cria Gold DDL, popula dimensoes e fatos

[6/6] Valida 7 KPIs contra gabarito.json
```

### Saida esperada

```
[1/6] Iniciando containers (postgres + pgadmin)...
[2/6] Aguardando banco ficar pronto...
       banco pronto
[3/6] Criando DDL Bronze...
[4/6] Carregando dados Bronze (~3.7M linhas, pode demorar 3-5 min)...
      Bronze concluido: 3,723,595 linhas em 9.4s  |  erros: 0
[5/6] Transformando Silver e populando Gold...
[6/6] Validando 7 KPIs contra gabarito...

  KPI 1: OK   KPI 2_3: OK   KPI 4: OK
  KPI 5: OK   KPI 6: OK     KPI 7: OK   KPI 8: OK

Setup concluido!
  pgAdmin : http://localhost:5051  (admin@banvic.com / admin)
  Postgres: localhost:5433         (banvic_user / banvic_pass)
```

---

## Como o Docker resolve "na minha maquina funciona"

Todo programador ja viveu: voce escreve o pipeline, testa no seu computador, manda para o servidor — e ele quebra. Versao diferente do Python, falta de um driver, configuracao diferente do banco.

Docker resolve isso empacotando nao so o codigo, mas o **ambiente inteiro**.

### Caracteristicas deste ambiente

**1. Init automatico via `docker-entrypoint-initdb.d`**

O Postgres executa automaticamente qualquer `.sql` nessa pasta ao criar o banco:

```yaml
volumes:
  - ./init:/docker-entrypoint-initdb.d:ro
```

O `init/01_setup.sql` cria schemas e extensoes antes de qualquer dado ser inserido.

**2. Persistencia com volume nomeado**

```yaml
volumes:
  - pgdata04:/var/lib/postgresql/data
```

Os dados sobrevivem a `docker compose down` e ao reinicio dos containers. Use
`docker compose down -v` somente quando quiser apagar o banco e recomecar do zero.

**3. Healthcheck — dependencia real, nao tempo fixo**

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U banvic_user -d banvic"]
  interval: 10s
  retries: 5
```

O pgAdmin so sobe quando o banco esta **realmente** aceitando conexoes — nao quando o processo iniciou.

**4. pgAdmin pre-configurado via `servers.json`**

```json
{
  "Servers": {
    "1": {
      "Name": "BanVic PostgreSQL",
      "Host": "banvic-p04-postgres",
      "Port": 5432,
      "Username": "banvic_user"
    }
  }
}
```

Sem precisar configurar manualmente: abra `http://localhost:5051`, faca login e o servidor ja aparece conectado.

**5. Volumes montados como somente leitura**

Os arquivos SQL do projeto sao montados no container (`/sql/`, `/proj01sql/`) sem copiar — mudancas no host aparecem imediatamente, sem rebuild da imagem.

---

## Infra base (docker-compose.yml raiz)

O `docker-compose.yml` na raiz do projeto sobe o ambiente que os outros projetos usam (Hop, Airflow, n8n):

```
banvic-base-postgres  — PostgreSQL 15, porta 5432
banvic-base-pgadmin   — pgAdmin4, porta 5050
banvic_net       — rede interna compartilhada
```

Para subir:
```bash
docker compose up -d   # na raiz do projeto
```

Os outros projetos usam `banvic_net: external: true` para se conectar ao mesmo banco sem duplicar infraestrutura.

---

## Deploy em servidor real (VPS)

```bash
# 1. Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Clonar e configurar
git clone <repo>
cd banvic-360
cp .env.example .env && nano .env

# 3. Subir
docker compose up -d
python scripts/entrypoint.py
```

Os dados ficam num volume Docker — reiniciar o servidor nao perde nada.

### Backup

```bash
# Backup diario as 2h (adicionar ao cron)
0 2 * * * docker exec banvic-base-postgres pg_dump -U banvic_user banvic \
  | gzip > /backups/banvic_$(date +%Y%m%d).sql.gz
```

---

## Troubleshooting

**"Port 5433 already in use"**
```bash
# Verificar o que esta usando a porta
lsof -i :5433   # Linux/Mac
netstat -ano | findstr :5433   # Windows
```

**Container sobe mas SQL falha**
```bash
docker compose logs postgres --tail 30
```

**pgAdmin nao mostra o servidor pre-configurado**
```bash
# Recriar somente o container do pgAdmin
docker compose up -d --force-recreate pgadmin
```
