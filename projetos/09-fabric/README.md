# Projeto 9 — Microsoft Fabric + Power BI

Este projeto fará o mesmo pipeline do BanVic usando o **Microsoft Fabric** — a plataforma integrada da Microsoft que combina engenharia de dados, ciência de dados e visualização num único lugar.

**Pergunta principal:** _Como entregar os dados diretamente no dashboard do gestor, sem precisar de ferramentas separadas?_

> **Status:** Em desenvolvimento. Este projeto será adicionado em breve.

---

## O que é o Microsoft Fabric

O Microsoft Fabric é como ter o Azure Data Factory, Synapse Analytics, Power BI e OneLake todos integrados numa única plataforma. Em vez de conectar ferramentas diferentes, tudo está no mesmo lugar.

Para quem já usa ferramentas Microsoft (Excel, Teams, Power BI), o Fabric é a evolução natural: os dados chegam no OneLake, são transformados em notebooks ou pipelines visuais, e aparecem automaticamente no Power BI — sem exportar, sem copiar, sem esperar.

---

## O que este projeto vai cobrir

- Ingestão dos dados do BanVic no **OneLake** (o data lake do Fabric)
- Transformação Bronze → Silver → Gold em **Spark notebooks** (similar ao Projeto 7)
- Modelagem dimensional em **Lakehouse tables**
- Criação das **8 KPIs em Power BI** com gráficos interativos
- Agendamento automático via **Data Factory pipelines**
- Comparação com o gabarito para validar os resultados

---

## Por que o Fabric é diferente dos outros

| Aspecto | Projetos 1-8 | Microsoft Fabric |
|---|---|---|
| Ferramentas | Várias separadas (PostgreSQL, Airflow, dbt...) | Tudo integrado numa plataforma |
| Destino final dos dados | Banco, arquivos | Power BI diretamente |
| Quem consome os dados | Engenheiros, analistas com SQL | Gestores, diretores, qualquer pessoa |
| Custo | Gratuito ou baixo | Por usuário/mês (requer conta Microsoft) |
| Onde roda | Local ou nuvem | Sempre na nuvem (Azure) |

---

## Pré-requisitos (quando disponível)

- Conta Microsoft com acesso ao **Microsoft Fabric** (disponível no portal.fabric.microsoft.com)
- Os CSVs do BanVic (Drive: https://drive.google.com/drive/folders/1mtIBYJss1RqkfT_trxrcH5nanoiBHiuq?usp=sharing)

O Microsoft Fabric tem um **trial gratuito de 60 dias** — suficiente para completar este projeto.

---

## Quando usar Microsoft Fabric

| Situação | Faz sentido? |
|---|---|
| Organização que já usa Microsoft 365 / Azure | Sim — integração nativa |
| Precisar entregar dashboards para gestores sem SQL | Sim — Power BI direto no Fabric |
| Dados acima de 100 GB com processamento distribuído | Sim — Spark integrado |
| Time pequeno sem infraestrutura própria | Sim — tudo gerenciado |
| Budget zero e dados locais | Não — use PostgreSQL + dbt (Projetos 1/6) |
| Organização que usa AWS ou GCP | Com cuidado — Fabric é Azure-first |

---

## Acompanhe a evolução do projeto

Este README será atualizado conforme o projeto for desenvolvido. Acompanhe o repositório para novidades.
