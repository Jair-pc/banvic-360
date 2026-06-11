# Projeto 4 — Docker + Ambiente

Este projeto não cria um novo pipeline — ele explica como o BanVic 360 usa Docker para garantir que tudo funcione igual em qualquer máquina, e como você levaria isso para um servidor real na internet.

**Pergunta principal:** _Como fazer o pipeline rodar igual no meu computador, no computador do colega e num servidor na nuvem?_

---

## O problema que o Docker resolve

Todo programador já viveu isso: "na minha máquina funciona". Você escreve o pipeline, testa no seu computador, manda para o servidor — e ele quebra. Versão diferente do Python, falta de um driver, configuração diferente do banco.

Docker resolve isso empacotando não só o código, mas o ambiente inteiro: a versão do Python, do PostgreSQL, das bibliotecas, das configurações. Quem baixar o projeto e tiver Docker instalado vai ter exatamente o mesmo ambiente que você.

---

## Como o Docker está organizado aqui

### Infraestrutura base (`docker-compose.yml` na raiz)

Sobe dois serviços que todos os projetos usam:

```
banvic_postgres  ← Banco de dados PostgreSQL 15, porta 5432
banvic_pgadmin   ← Interface visual do banco, porta 5050 (http://localhost:5050)
```

Os dois ficam na mesma rede interna (`banvic_net`) — o pgAdmin fala com o Postgres pelo nome `banvic_postgres`, não pelo IP. Isso é importante: o nome funciona igual em qualquer máquina.

O banco tem um **healthcheck** — outros serviços só sobem depois que o banco está realmente pronto, não só quando o processo iniciou.

### Projeto 3 (`projetos/03-apache-hop/docker-compose.yml`)

O Apache Hop roda em seu próprio arquivo docker-compose e se conecta à rede que já existe:

```yaml
networks:
  banvic_net:
    external: true  # usa a rede que a raiz criou
```

O container do Hop enxerga o banco pelo hostname `banvic_postgres` — o mesmo que usaria em produção. Você não muda o código para trocar de ambiente.

---

## Deploy em um servidor real (VPS)

Se você quiser colocar o BanVic num servidor na internet (DigitalOcean, AWS, Hetzner...), o processo é direto.

### 1. Criar o servidor

Qualquer Linux recente funciona. Recomendado: Ubuntu 22.04 LTS, 2 CPUs, 4 GB RAM.

```bash
# Instalar Docker no servidor
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. Trazer o projeto para o servidor

```bash
git clone https://github.com/seu-usuario/banvic-360.git
cd banvic-360
cp .env.example .env
nano .env   # editar com as senhas corretas
```

### 3. Subir os containers

```bash
docker compose up -d
```

Os dados ficam num volume Docker — reiniciar o servidor não perde nada.

### 4. Carregar os dados

```bash
pip install -r requirements.txt
# Baixar dados do Drive para data/ e external_data/
python scripts/entrypoint.py
```

---

## Boas práticas de segurança

### Senhas nunca no código

O arquivo `.env` tem as senhas do banco. Ele está no `.gitignore` — nunca vai para o GitHub. No servidor, use `chmod 600 .env` para que só você consiga ler.

Em sistemas profissionais, as senhas ficam em serviços específicos para isso:

| Onde guardar senhas | Quando usar |
|---|---|
| Docker Secrets | Docker Swarm (múltiplos servidores) |
| AWS Secrets Manager | Projetos na AWS |
| GitHub Actions Secrets | Só durante deploy automático |
| `.env` com `chmod 600` | Projetos pessoais em servidor simples |

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
