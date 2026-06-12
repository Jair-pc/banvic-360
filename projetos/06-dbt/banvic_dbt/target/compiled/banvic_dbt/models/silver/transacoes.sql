

select
    cod_transacao::integer              as cod_transacao,
    num_conta::integer                  as num_conta,
    data_transacao::timestamp           as data_transacao,
    date_trunc('month', data_transacao::timestamp)::date as mes_referencia,
    trim(nome_transacao)                as nome_transacao,
    valor_transacao::numeric(14,2)      as valor_transacao,
    abs(valor_transacao::numeric)       as valor_absoluto,
    case when valor_transacao::numeric >= 0 then true else false end as flag_credito,
    case
        when nome_transacao ilike '%pix%'      then 'Pix'
        when nome_transacao ilike '%ted%'      then 'TED'
        when nome_transacao ilike '%doc%'      then 'DOC'
        when nome_transacao ilike '%credito%'  then 'Compra Credito'
        when nome_transacao ilike '%debito%'   then 'Compra Debito'
        when nome_transacao ilike '%saque%'    then 'Saque'
        when nome_transacao ilike '%deposito%' then 'Deposito Especie'
        when nome_transacao ilike '%boleto%'   then 'Pagamento Boleto'
        else 'Outros'
    end                                 as canal
from "banvic"."bronze"."transacoes"
where cod_transacao is not null
  and valor_transacao ~ '^-?[0-9]+\.?[0-9]*$'
  and valor_transacao::numeric <> 0