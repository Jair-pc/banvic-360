

select
    cli.faixa_etaria,
    count(distinct cli.sk_cliente)             as qtd_clientes,
    round(avg(fc.saldo_total)::numeric, 2)     as saldo_medio,
    round(sum(fc.saldo_total)::numeric, 2)     as saldo_total
from "banvic"."gold"."dim_cliente" cli
left join "banvic"."gold"."fato_contas" fc
    on fc.sk_cliente = cli.sk_cliente
    and fc.eh_conta_ativa = true
where cli.eh_registro_atual = true
group by cli.faixa_etaria
order by cli.faixa_etaria