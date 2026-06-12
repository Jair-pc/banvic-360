

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
from "banvic"."silver"."transacoes" tx
join "banvic"."gold"."dim_tempo" t
    on t.data = tx.data_transacao::date
join "banvic"."silver"."contas" c
    on c.num_conta = tx.num_conta
join "banvic"."gold"."dim_cliente" cli
    on cli.cod_cliente = c.cod_cliente
   and cli.eh_registro_atual = true
join "banvic"."gold"."dim_agencia" ag
    on ag.cod_agencia = c.cod_agencia
left join "banvic"."gold"."dim_canal" can
    on can.nome_canal = tx.canal