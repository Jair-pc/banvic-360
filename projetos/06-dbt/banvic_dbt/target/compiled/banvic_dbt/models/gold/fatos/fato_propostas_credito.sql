

-- Lê diretamente do Bronze (não do Silver) para manter o grain de
-- 1.996 propostas originais — consistente com o gabarito.

select
    p.cod_proposta::integer             as cod_proposta,
    t.sk_tempo                          as sk_tempo_entrada,
    cli.sk_cliente,
    col.sk_colaborador,
    p.status_proposta,
    p.valor_proposta::numeric           as valor_proposta,
    p.valor_financiamento::numeric      as valor_financiamento,
    p.valor_entrada::numeric            as valor_entrada,
    p.valor_prestacao::numeric          as valor_prestacao,
    p.quantidade_parcelas::smallint     as quantidade_parcelas,
    p.taxa_juros_mensal::numeric        as taxa_juros_mensal
from "banvic"."bronze"."propostas_credito" p
join "banvic"."gold"."dim_tempo" t
    on t.data = p.data_entrada_proposta::date
join "banvic"."gold"."dim_cliente" cli
    on cli.cod_cliente = p.cod_cliente::integer
   and cli.eh_registro_atual = true
left join "banvic"."gold"."dim_colaborador" col
    on col.cod_colaborador = p.cod_colaborador::integer
where p.cod_proposta is not null
  and p.data_entrada_proposta is not null