{{ config(materialized='table', schema='gold') }}

select
    tx.cod_transacao,
    t.sk_tempo,
    cli.sk_cliente,
    ag.sk_agencia,
    can.sk_canal,
    tx.num_conta,
    tx.nome_transacao,
    tx.valor_transacao,
    tx.flag_credito
from {{ ref('transacoes') }} tx
join {{ ref('dim_tempo') }} t
    on t.data = tx.data_transacao::date
join {{ ref('contas') }} c
    on c.num_conta = tx.num_conta
join {{ ref('dim_cliente') }} cli
    on cli.cod_cliente = c.cod_cliente
   and cli.eh_registro_atual = true
join {{ ref('dim_agencia') }} ag
    on ag.cod_agencia = c.cod_agencia
left join {{ ref('dim_canal') }} can
    on can.nome_canal = tx.canal
