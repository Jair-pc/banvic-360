{{ config(materialized='view', schema='gold') }}

select
    status_proposta,
    count(*)                            as qtd_propostas,
    round(avg(valor_proposta), 2)       as valor_medio_proposta,
    round(sum(valor_proposta), 2)       as valor_total_proposta
from {{ ref('fato_propostas_credito') }}
group by status_proposta
order by qtd_propostas desc
