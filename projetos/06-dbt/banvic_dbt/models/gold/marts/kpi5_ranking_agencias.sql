{{ config(materialized='view', schema='gold') }}

with volume_ag as (
    select
        ag.cod_agencia,
        round(sum(abs(ft.valor_transacao))::numeric, 2) as volume_total
    from {{ ref('fato_transacoes') }} ft
    join {{ ref('dim_agencia') }} ag on ag.sk_agencia = ft.sk_agencia
    group by ag.cod_agencia
)
select
    row_number() over (order by k1.saldo_total desc, coalesce(v.volume_total, 0) desc) as ranking,
    k1.cod_agencia,
    k1.nome_agencia,
    k1.qtd_contas,
    round(k1.saldo_total::numeric, 2)   as saldo_total,
    round(k1.saldo_medio::numeric, 2)   as saldo_medio,
    coalesce(v.volume_total, 0)         as volume_total
from {{ ref('kpi1_saldo_agencia') }} k1
left join volume_ag v on v.cod_agencia = k1.cod_agencia
