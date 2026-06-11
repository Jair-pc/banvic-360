# Projeto 4 — Docker + Ambiente

Este projeto não cria um novo pipeline — ele explica como o BanVic 360 usa Docker para garantir que tudo funcione igual em qualquer máquina, e como você levaria isso para um servidor real na internet.

**Pergunta principal:** _Como fazer o pipeline rodar igual no meu computador, no computador do colega e num servidor na nuvem?_

---

## O problema que o Docker resolve

Todo programador já viveu isso: **"na minha máquina funciona"**. Você escreve o pipeline, testa no seu computador, manda para o servidor — e ele quebra. Versão diferente do Python, falta de um driver, configuração diferente do banco.

Docker resolve isso empacotando não só o código, mas o **ambiente inteiro**: a versão do Python, do PostgreSQL, das bibliotecas, das configurações.

Quem baixar o projeto e tiver Docker instalado vai ter exatamente o mesmo ambiente que você, sem instalar mais nada.

---

## O que este projeto cobre

1. Como o `docker-compose.yml` da raiz funciona (PostgreSQL + pgAdmin)
2. Como os outros projetos se conectam ao mesmo banco
3. Como fazer deploy num servidor real (VPS)
4. Boas práticas de segurança (senhas, backups)
5. Deploy automático com GitHub Actions

---

## Como o Docker está organizado aqui

### Infraestrutura base (`docker-compose.yml` na raiz)

Sobe dois serviços que **todos os projetos usam**:

```
banvic_postgres  ← Banco de dados PostgreSQL 15, porta 5432
banvic_pgadmin   ← Interface visual do banco, porta 5050
```

Para subir:
```bash
docker compose up -d
```

Para acessar o pgAdmin:
- Abra `http://localhost:5050` no navegador
- Login: `admin@banvic.local`
- Senha: `admin`
- Servidor: `banvic_postgres` / Senha do banco: `banvic_pass`

Os dois containers ficam na mesma rede interna (`banvic_net`). O pgAdmin fala com o Postgres pelo **nome** `banvic_postgres`, não pelo IP. Isso é importante: o nome funciona igual em qualquer máquina.

### Healthcheck — por que é importante

O banco tem um healthcheck configurado:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U banvic_user -d banvic"]
  interval: 10s
  retries: 5
```

Isso significa: outros serviços só sobem depois que o banco está **realmente pronto** para aceitar conexões — não só quando o processo iniciou. Sem isso, o script Python tentaria conectar antes do banco estar pronto e falharia.

### Como os outros projetos se conectam

O Projeto 3 (Apache Hop), Projeto 5 (Airflow) e Projeto 8 (n8n) têm seus próprios `docker-compose.yml` que se conectam ao banco já criado:

```yaml
networks:
  banvic_net:
    external: true  # usa a rede que a raiz criou
```

O container enxerga o banco pelo hostname `banvic_postgres` — o mesmo que usaria em produção. Você não muda o código para trocar de ambiente.

---

## Verificar se está funcionando

```bash
# Ver containers rodando
docker ps

# Banco deve aparecer como "healthy"
# Se aparecer "starting", aguarde ~30 segundos

# Ver logs do banco
docker logs banvic_postgres --tail 20
```

---

## Deploy em um servidor real (VPS)

Se você quiser colocar o BanVic num servidor na internet (DigitalOcean, AWS, Hetzner...), o processo é direto.

### 1. Criar o servidor

Qualquer Linux recente funciona. Recomendado: Ubuntu 22.04 LTS, 2 CPUs, 4 GB RAM.

```bash
# Instalar Docker no servidor (rodar no servidor via SSH)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Sair e entrar novamente para o grupo funcionar
```

### 2. Trazer o projeto para o servidor

```bash
git clone https://github.com/Jair-pc/banvic-360.git
cd banvic-360
cp .env.example .env
nano .env   # editar com as senhas que você quiser
```

### 3. Subir os containers

```bash
docker compose up -d
```

Os dados ficam num volume Docker — **reiniciar o servidor não perde nada**.

### 4. Carregar os dados

```bash
pip install -r requirements.txt
# Baixar dados do Drive para data/ e external_data/
python scripts/entrypoint.py
```

---

## Boas práticas de segurança

### Senhas nunca no código

O arquivo `.env` tem as senhas do banco. Ele está no `.gitignore` — nunca vai para o GitHub.

No servidor:
```bash
chmod 600 .env   # só você consegue ler
```

Em sistemas profissionais, as senhas ficam em serviços específicos:

| Onde guardar senhas | Quando usar |
|---|---|
| `.env` com `chmod 600` | Projetos pessoais em servidor simples |
| Docker Secrets | Docker Swarm (múltiplos servidores) |
| AWS Secrets Manager | Projetos na AWS |
| GitHub Actions Secrets | Só durante deploy automático |

### Backup automático

```bash
# Esse comando, agendado no cron, faz backup todo dia às 2h
0 2 * * * docker exec banvic_postgres pg_dump -U banvic_user banvic \
  | gzip > /backups/banvic_$(date +%Y%m%d).sql.gz
```

---

## Deploy automático com GitHub Actions

Se você quiser que o servidor se atualize sozinho a cada push no GitHub:

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
            docker compose up -d
```

As credenciais ficam nos Secrets do GitHub — nunca no código.

---

## Monitorar o que está rodando

```bash
# Ver todos os containers ativos
docker ps

# Ver logs do banco (últimas 50 linhas)
docker logs banvic_postgres --tail 50

# Ver uso de CPU e memória em tempo real
docker stats

# Parar tudo
docker compose down

# Parar tudo e apagar os dados (cuidado!)
docker compose down -v
```

---

## Se algo não funcionar

**"Docker daemon is not running"**
- Abra o Docker Desktop e aguarde iniciar

**"Port 5432 is already in use"**
```bash
# Outro PostgreSQL está usando a porta. Para ele ou mude a porta no .env:
# POSTGRES_PORT=5433
```

**"Permission denied" ao rodar docker**
```bash
sudo usermod -aG docker $USER   # Linux
# Depois sair e entrar novamente
```

---

## Quando Docker faz diferença

| Situação | Docker ajuda? |
|---|---|
| Compartilhar o projeto com alguém | Sim — um `docker compose up` e funciona |
| Deploy num servidor | Sim — sem instalar nada manualmente |
| Pipeline com dependências conflitantes | Sim — cada serviço tem seu ambiente isolado |
| Reproduzir um bug que aconteceu em produção | Sim — ambiente idêntico |
| Banco em produção de alta criticidade | Cuidado — prefira um banco gerenciado (RDS, Cloud SQL) |
