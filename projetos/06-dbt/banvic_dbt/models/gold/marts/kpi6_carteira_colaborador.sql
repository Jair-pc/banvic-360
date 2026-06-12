{{ config(materialized='view', schema='gold') }}

with contas_por_col as (
    select
        sk_colaborador,
        count(distinct num_conta) as qtd_contas,
        sum(saldo_total)          as saldo_total
    from {{ ref('fato_contas') }}
    where eh_conta_ativa = true
    group by sk_colaborador
),
propostas_por_col as (
    select
        sk_colaborador,
        count(distinct cod_proposta)                                              as qtd_propostas,
        count(distinct cod_proposta) filter (where status_proposta = 'Aprovada') as propostas_aprovadas
    from {{ ref('fato_propostas_credito') }}
    group by sk_colaborador
)
select
    col.cod_colaborador,
    trim(col.primeiro_nome || ' ' || col.ultimo_nome) as nome,
    col.cargo,
    ag.nome                                        as agencia,
    coalesce(cc.qtd_contas, 0)                     as qtd_contas_geridas,
    round(coalesce(cc.saldo_total, 0)::numeric, 2) as saldo_gerido,
    coalesce(pc.qtd_propostas, 0)                  as qtd_propostas,
    coalesce(pc.propostas_aprovadas, 0)            as propostas_aprovadas
from {{ ref('dim_colaborador') }} col
join {{ ref('dim_agencia') }} ag    on ag.sk_agencia = col.sk_agencia_principal
left join contas_por_col cc         on cc.sk_colaborador = col.sk_colaborador
left join propostas_por_col pc      on pc.sk_colaborador = col.sk_colaborador
where col.eh_ativo = true
order by saldo_gerido desc nulls last
