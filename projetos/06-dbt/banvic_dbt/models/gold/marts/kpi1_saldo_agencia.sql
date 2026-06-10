{{ config(materialized='view', schema='gold') }}

select
    ag.cod_agencia,
    ag.nome                                         as nome_agencia,
    count(fc.num_conta)                             as qtd_contas,
    round(sum(fc.saldo_total), 2)                   as saldo_total,
    round(avg(fc.saldo_total), 2)                   as saldo_medio,
    rank() over (order by sum(fc.saldo_total) desc) as ranking
from {{ ref('fato_contas') }} fc
join {{ ref('dim_agencia') }} ag on ag.sk_agencia = fc.sk_agencia
group by ag.cod_agencia, ag.nome
order by ranking
