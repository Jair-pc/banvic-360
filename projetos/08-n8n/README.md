# Projeto 8 — n8n: Automação Visual

Este projeto faz o mesmo pipeline do BanVic usando o **n8n** — uma ferramenta de automação visual onde você monta fluxos de trabalho conectando blocos na tela, sem precisar programar.

**Pergunta principal:** _O que muda quando qualquer pessoa do time consegue entender e modificar o pipeline?_

---

## O que é o n8n

n8n é como o Zapier ou Make (Integromat), mas que você instala no seu próprio servidor. Você conecta serviços diferentes — banco de dados, APIs, e-mail, Slack — arrastando blocos e configurando campos.

O resultado é visual e interativo: você vê cada bloco ficando verde (sucesso) ou vermelho (erro) em tempo real enquanto o pipeline executa.

---

## Por que o n8n é diferente do Airflow

Ambos agendam e orquestram pipelines. A diferença é quem consegue usar:

| Aspecto | Airflow (Projeto 5) | n8n (Projeto 8) |
|---|---|---|
| Como você define o pipeline | Código Python | Arrastar blocos na tela |
| Modificar um passo | Editar arquivo + novo deploy | Clicar no bloco + salvar |
| Ver o fluxo funcionando | Diagrama estático | Animação em tempo real |
| Lidar com erros | `try/except` no código | Bloco `IF` com seta vermelha |
| Enviar alerta por e-mail ou Slack | Configurar no código | Bloco nativo, pronto |
| Quem consegue manter | Engenheiro de dados | Engenheiro + Analista + Operações |

**O resultado é o mesmo. O caminho é diferente. A audiência é diferente.**

---

## Resultado

| KPI | Resultado |
|---|---|
| KPI 1 — Saldo total | R$ 26.509.620,12 (10 agências) |
| KPI 2 — Volume de transações | R$ 58.122.708,67 (71.921 tx, 155 meses) |
| KPI 4 — Propostas | 525 Enviada / 513 Aprovada / 490 Validação / 468 Em análise |

---

## Arquivos do projeto

```
projetos/08-n8n/
├── workflows/
│   ├── 01_pipeline_banvic.json   Pipeline completo: Bronze → Silver → Gold → KPI
│   └── 02_validar_kpis.json      Validação standalone (Gold já populado)
├── Dockerfile                    n8n + psql + python3 (imagem customizada)
├── docker-compose.yml            n8n + PostgreSQL em rede isolada
├── .env.example                  Configurações
└── run.bat                       Windows: sobe tudo
```

---

## Como executar

### Pré-requisitos

- Docker Desktop instalado e rodando
- CSVs do BanVic disponíveis (veja como obter na raiz do projeto)

### 1. Subir os containers

**Windows:**
```bat
cd projetos\08-n8n
run.bat
```

**Linux/Mac:**
```bash
cd projetos/08-n8n
cp .env.example .env
docker compose up -d --build
```

O build pode demorar 2-3 minutos na primeira vez (baixa a imagem do n8n).

### 2. Acessar o n8n

Abra `http://localhost:5678` no navegador.
- Login: `admin`
- Senha: `banvic2024`

**O que você vai ver:** a interface do n8n com espaço em branco. Os workflows ainda não foram importados.

### 3. Importar os workflows

```
Menu lateral → Settings → Import from file
→ Selecionar: workflows/01_pipeline_banvic.json

Menu lateral → Settings → Import from file
→ Selecionar: workflows/02_validar_kpis.json
```

Depois do import, dois workflows aparecem na lista.

### 4. Configurar a conexão com o banco

```
Menu lateral → Credentials → Add Credential → PostgreSQL
  Nome:     BanVic PostgreSQL
  Host:     postgres
  Port:     5432
  Database: banvic
  User:     banvic_user
  Password: banvic_pass
```

Clique em **Test** para verificar se conectou. Deve aparecer "Connection successful".

### 5. Carregar os dados Bronze (se necessário)

```bash
docker exec banvic_n8n python3 /data/banvic/scripts/carga_bronze.py
```

### 6. Executar o pipeline

Abra o workflow `BanVic 360 - Pipeline ETL Completo` → clique em **Execute Workflow**.

Observe os blocos ficando verdes em tempo real. Se um bloco ficar vermelho, clique nele para ver o erro.

---

## Como o pipeline está organizado

```
[Executar Manualmente]
[Agendamento Diário 02h]   ← mesmas entradas, fluxo unificado
         ↓
[Verificar Bronze]         ← garante que os dados chegaram
         ↓
[Silver: Limpeza]          ← chama o SQL do Projeto 1
         ↓
[Gold: Dimensões]          ← chama o SQL do Projeto 1
         ↓
[Gold: Fatos]              ← chama o SQL do Projeto 1
         ↓
[KPI 1: Saldo por Agência] ← consulta direta no banco
         ↓
[Validar vs Gabarito]      ← JavaScript: compara o resultado
         ↓
[Aprovado?]                ← bloco IF com duas saídas
    ↓              ↓
[Sucesso]      [Falhou: envia alerta]
```

---

## Por que o n8n reutiliza o SQL do Projeto 1

Os blocos `Execute Command` chamam os mesmos arquivos SQL que já existem:

```bash
psql -f /data/banvic/sql/02_silver/ddl_silver_transforms.sql
psql -f /data/banvic/projetos/01-sql-puro/sql/01_populate_dims.sql
psql -f /data/banvic/projetos/01-sql-puro/sql/02_populate_fatos.sql
```

Isso mostra o papel correto do n8n: ele é um **orquestrador**, não um reescritor. Você não joga fora o SQL que já funciona — você o agenda e monitora visualmente.

---

## Se algo não funcionar

**n8n não abre em localhost:5678**
```bash
docker ps   # verifique se banvic_n8n está na lista
docker logs banvic_n8n --tail 30   # veja o log de inicialização
```

**"Credential not found" ao executar o workflow**
```
O workflow foi importado mas a credencial não foi criada ainda.
Volte ao Passo 4 e configure a credencial PostgreSQL.
```

**Bloco vermelho "Execute Command"**
```
O script SQL não conseguiu conectar ao banco.
Verifique se o container postgres está rodando:
docker ps | grep postgres
```

**"Table does not exist" no bloco Silver**
```bash
# Bronze não foi carregado
docker exec banvic_n8n python3 /data/banvic/scripts/carga_bronze.py
```

---

## Quando usar n8n

| Situação | Faz sentido? |
|---|---|
| Time misto (devs + analistas + operações) | Sim — todos conseguem entender |
| Integrações com APIs, webhooks, e-mail, Slack | Sim — blocos nativos para tudo |
| Pipelines simples a médios | Sim — zero overhead de infraestrutura |
| DAGs com centenas de tarefas complexas | Não — Airflow é mais robusto |
| Transformações pesadas em Python | Não — Airflow ou Projeto 2 |
| Volume acima de 100 GB | Não — Databricks (Projeto 7) |
| Notificações e alertas operacionais | Sim — bloco de e-mail/Slack nativo |
