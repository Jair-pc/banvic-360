# Projeto 4 — Docker + Ambiente

Documentação de como o BanVic 360 usa Docker — e como essa mesma estrutura
funcionaria em um ambiente real de produção, em uma VPS ou nuvem.

**Pergunta central:** _Como garantir que o pipeline roda igual em qualquer máquina — da local à produção?_

---

## O que o Docker resolve aqui

Engenharia de dados tem um problema clássico: o pipeline funciona na sua máquina,
não funciona no servidor, não funciona na máquina do colega. Docker elimina essa
variabilidade empacotando não só o código, mas o ambiente inteiro — versão do Python,
versão do PostgreSQL, variáveis de ambiente, drivers de banco.

No BanVic 360, a cadeia toda depende de:

- PostgreSQL 15 com schemas específicos e extensões (`uuid-ossp`, `unaccent`)
- Python 3.10+ com psycopg2, pandas, SQLAlchemy, faker
- Apache Hop 2.10 com metadados de conexão pré-configurados
- Rede interna entre containers (o Hop precisa enxergar o Postgres pelo hostname, não por `localhost`)

Tudo isso está declarado em arquivos versionados. Não há nada para "instalar manualmente".

---

## Como o Docker está organizado no projeto

### Raiz do projeto (`docker-compose.yml`)

Sobe a infraestrutura base que todos os projetos compartilham:

```
banvic_postgres   ← PostgreSQL 15, porta 5432, volume persistente
banvic_pgadmin    ← pgAdmin 4, porta 5050
```

Rede interna: `banvic_net` (bridge). Todos os containers que precisam do Postgres
se conectam a essa rede — sem expor o banco para fora do Docker.

```yaml
# trecho relevante
services:
  postgres:
    image: postgres:15
    container_name: banvic_postgres
    environment:
      POSTGRES_DB: banvic
      POSTGRES_USER: banvic_user
      POSTGRES_PASSWORD: banvic_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U banvic_user -d banvic"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - banvic_net

networks:
  banvic_net:
    name: banvic_net
    driver: bridge
```

O `healthcheck` é importante: outros containers que dependem do Postgres
só sobem quando o banco está pronto para aceitar conexões, não só quando o processo iniciou.

### Projeto 3 (`projetos/03-apache-hop/docker-compose.yml`)

O Hop roda em seu próprio compose e se conecta à rede existente como `external: true`:

```yaml
networks:
  banvic_net:
    external: true
    name: banvic_net
```

Isso permite que o container `banvic_hop` resolva `banvic_postgres` pelo hostname —
o mesmo nome que estaria em produção. O código não muda entre ambientes.

---

## Deploy em VPS

O processo para levar isso para uma VPS (DigitalOcean Droplet, AWS EC2, Hetzner, etc.)
é direto, sem surpresas:

### 1. Provisionar a VPS

Qualquer distribuição Linux recente funciona. Ubuntu 22.04 LTS é o mais seguro.
Mínimo para desenvolvimento/portfólio: 2 vCPU, 4 GB RAM, 40 GB SSD.

```bash
# Instalar Docker e Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. Transferir o projeto

```bash
# Via git (recomendado — os dados ficam no Drive, não no repo)
git clone https://github.com/Jair-pc/banvic-360.git
cd banvic-360

# Criar o .env com as variáveis de produção
cp .env.example .env
nano .env
```

### 3. Subir os containers

```bash
docker compose up -d
```

O volume `postgres_data` persiste em `/var/lib/docker/volumes/` na VPS.
Reinicializações da máquina não perdem dados.

### 4. Carregar os dados

```bash
# Instalar dependências Python (ou usar um container Python)
pip install -r requirements.txt

# Baixar dados do Drive para data/ e external_data/
# Em seguida:
python scripts/entrypoint.py
```

---

## Boas práticas para produção

### Segredos: nunca no `.env` commitado

Em produção, senhas e chaves não ficam em arquivos `.env` no servidor.
As alternativas mais comuns:

| Abordagem | Quando usar |
|---|---|
| Docker Secrets | Docker Swarm — segredos montados como arquivos em `/run/secrets/` |
| AWS Secrets Manager / Parameter Store | Deploy na AWS |
| HashiCorp Vault | Ambientes maiores com auditoria de acesso |
| GitHub Actions Secrets | Senhas usadas só no CI/CD |

Para um projeto solo em VPS simples, o mínimo aceitável é:
- `.env` fora do repositório (no `.gitignore`)
- Permissões `chmod 600 .env` no servidor
- Acesso SSH com chave, não senha

### Volumes e backup

O PostgreSQL persiste em volume nomeado. Para backup automatizado:

```bash
# Dump diário via cron
0 2 * * * docker exec banvic_postgres pg_dump -U banvic_user banvic \
  | gzip > /backups/banvic_$(date +%Y%m%d).sql.gz
```

Para retenção, um script apaga dumps com mais de 30 dias.

### Atualizações sem downtime

Para projetos de dados (não APIs em tempo real), o ciclo típico é:

```bash
git pull
docker compose down
docker compose up -d
python scripts/entrypoint.py  # recarrega se necessário
```

Se o pipeline rodar em schedule (Projeto 5 — Airflow), o processo é o mesmo,
mas o Airflow gerencia quando reexecutar após o container voltar.

---

## CI/CD com GitHub Actions

Para automatizar o deploy ao fazer push na branch `main`:

```yaml
# .github/workflows/deploy.yml
name: Deploy BanVic

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd ~/banvic-360
            git pull
            docker compose up -d --no-deps postgres
```

As senhas do banco ficam nos Secrets do GitHub, nunca no código.
O deploy apenas atualiza o código e reinicia os containers necessários.

---

## Monitoramento básico

Para saber se os containers estão rodando:

```bash
# Status de todos os containers
docker ps

# Logs do Postgres (últimas 50 linhas)
docker logs banvic_postgres --tail 50

# Uso de recursos
docker stats
```

Para alertas em caso de queda, a abordagem mais simples é um healthcheck
via cron que manda e-mail ou notificação no Slack se o container não responder:

```bash
# Verificar a cada 5 minutos
*/5 * * * * docker exec banvic_postgres pg_isready -U banvic_user \
  || curl -s -X POST "$SLACK_WEBHOOK" -d '{"text":"banvic_postgres caiu"}'
```

---

## `.dockerignore`

Para não enviar arquivos desnecessários ao build context (quando se usa `Dockerfile`):

```
data/
external_data/
*.csv
*.log
.env
__pycache__/
.git/
docs/
```

Os dados ficam fora da imagem — são montados via volume ou baixados no runtime.

---

## Quando Docker faz diferença

| Situação | Docker ajuda? |
|---|---|
| Compartilhar ambiente com um colega | **Sim** — `git clone` + `docker compose up` e pronto |
| Deploy em VPS sem instalações manuais | **Sim** — tudo declarado em arquivo |
| Rodar o mesmo pipeline em CI/CD | **Sim** — mesma imagem, comportamento previsível |
| Pipeline com dependências conflitantes | **Sim** — cada serviço tem seu próprio ambiente |
| Performance máxima em banco | **Não** — Postgres em container tem overhead mínimo vs bare-metal |
| Persistência de dados críticos | **Com cuidado** — volumes Docker precisam de backup explícito |

Docker não substitui um banco gerenciado (RDS, Cloud SQL) em produção de alta criticidade.
O valor aqui é reproducibilidade e portabilidade — que é exatamente o que um portfólio precisa demonstrar.
