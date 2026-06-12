

select
    cod_proposta::integer               as cod_proposta,
    cod_cliente::integer                as cod_cliente,
    cod_colaborador::integer            as cod_colaborador,
    data_entrada_proposta::date         as data_entrada_proposta,
    taxa_juros_mensal::numeric(8,6)     as taxa_juros_mensal,
    valor_proposta::numeric(14,2)       as valor_proposta,
    valor_financiamento::numeric(14,2)  as valor_financiamento,
    valor_entrada::numeric(14,2)        as valor_entrada,
    valor_prestacao::numeric(14,2)      as valor_prestacao,
    quantidade_parcelas::smallint       as quantidade_parcelas,
    coalesce(nullif(carencia,'')::smallint, 0) as carencia_dias,
    trim(status_proposta)               as status_proposta
from "banvic"."bronze"."propostas_credito"
where cod_proposta is not null
  and valor_proposta ~ '^[0-9]+\.?[0-9]*$'

union all

select
    cod_proposta::integer, cod_cliente::integer, cod_colaborador::integer,
    data_entrada_proposta::date,
    taxa_juros_mensal::numeric(8,6),
    valor_proposta::numeric(14,2), valor_financiamento::numeric(14,2),
    valor_entrada::numeric(14,2), valor_prestacao::numeric(14,2),
    quantidade_parcelas::smallint,
    coalesce(nullif(carencia,'')::smallint, 0),
    trim(status_proposta)
from "banvic"."bronze"."propostas_sinteticas"
where cod_proposta is not null