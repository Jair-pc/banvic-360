{{ config(materialized='table', schema='gold') }}

select
    row_number() over (order by canal)::integer         as sk_canal,
    canal                                               as nome_canal,
    case
        when canal in ('Pix', 'TED', 'DOC')                  then 'Transferencia'
        when canal in ('Compra Credito', 'Compra Debito')     then 'Cartao'
        when canal in ('Saque', 'Deposito Especie')           then 'Caixa'
        when canal = 'Pagamento Boleto'                       then 'Boleto'
        else 'Digital'
    end                                                 as tipo_canal
from (
    select distinct canal
    from {{ ref('transacoes') }}
    order by canal
) t
