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

**O que são os arquivos `.hpl` e `.hwf`?** São os arquivos do Apache Hop. `.hpl` é um pipeline (sequência de transformações). `.hwf` é um workflow (orquestrador que chama os pipelines na ordem certa). Você pode abri-los na interface visual do Hop para ver o diagrama.

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

### Rodar via Docker (recomendado — sem instalar o Hop)

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

**O que você vai ver na tela (tempo real: ~18 segundos):**
```
2026/06/12 13:59:37 - 00_banvic_pipeline - Starting action [Preparar ambiente]
2026/06/12 13:59:37 - 00_banvic_pipeline - Starting action [01 Silver]
2026/06/12 13:59:39 - 01_silver - Pipeline duration : 1.659 seconds
2026/06/12 13:59:39 - 00_banvic_pipeline - Starting action [02 Gold Dims]
2026/06/12 13:59:49 - 02_gold_dims - Pipeline duration : 10.683 seconds
2026/06/12 13:59:50 - 00_banvic_pipeline - Starting action [03 Gold Fatos]
2026/06/12 13:59:54 - 03_gold_fatos - Pipeline duration : 4.274 seconds
2026/06/12 13:59:54 - 00_banvic_pipeline - Starting action [Sucesso]
2026/06/12 13:59:54 - 00_banvic_pipeline - Workflow duration : 18.195 seconds
```

### Ver o pipeline visualmente (opcional)

Para ver o diagrama dos pipelines na interface do Hop:

1. Baixe o Apache Hop em [hop.apache.org](https://hop.apache.org/download/)
2. Abra o aplicativo `hop-gui.bat` (Windows) ou `hop-gui.sh` (Linux/Mac)
3. Vá em **File → Open Project** e aponte para `projetos/03-apache-hop/hop/`
4. Abra qualquer arquivo `.hpl` para ver o pipeline em blocos

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

### Fluxo de controle do workflow principal

```
Início
  ↓
[Limpar tabelas]   ← evita dados duplicados
  ↓ sucesso          ↓ erro
[Silver]           [PARAR + log de erro]
  ↓ sucesso          ↓ erro
[Gold Dimensões]   [PARAR + log de erro]
  ↓ sucesso          ↓ erro
[Gold Fatos]       [PARAR + log de erro]
  ↓
[Sucesso!]
```

---

## Se algo não funcionar

**"Cannot connect to banvic-base-postgres"**
```bash
# O banco precisa estar na rede banvic_net
docker network ls   # verifique se banvic_net existe
docker compose up -d   # na raiz do projeto
```

**Container Hop sobe mas não encontra os arquivos**
```bash
# Certifique que está rodando o run.bat de dentro da pasta do projeto
cd projetos\03-apache-hop
run.bat
```

**"Table does not exist" no pipeline Silver**
```bash
# Bronze não foi carregado ainda
python scripts/entrypoint.py   # na raiz do projeto
```

---

## Hop vs Código

| O que você precisa | Hop | Python/SQL |
|---|---|---|
| Ver o fluxo visualmente | Sim — arrastar e soltar | Não — precisa ler código |
| Modificar um passo | Clicar + editar campo | Editar arquivo de código |
| Debug (ver dados no meio) | Sim — preview de dados em cada bloco | `df.head()` ou logs |
| Rastreabilidade dos dados | Sim — nativo | Manual |
| Portabilidade entre bancos | Sim — troca só a conexão | Depende do código |
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
