{{ config(materialized='table', schema='silver') }}

select
    num_conta::integer                 as num_conta,
    cod_cliente::integer               as cod_cliente,
    cod_agencia::integer               as cod_agencia,
    cod_colaborador::integer           as cod_colaborador,
    trim(tipo_conta)                   as tipo_conta,
    data_abertura::date                as data_abertura,
    round(saldo_total::numeric, 2)          as saldo_total,
    round(saldo_disponivel::numeric, 2)     as saldo_disponivel,
    data_ultimo_lancamento::date            as data_ultimo_lancamento,
    case
        when data_ultimo_lancamento::date >=
             (select max(data_ultimo_lancamento::date) from {{ source('bronze', 'contas') }}) - 90
        then true else false
    end                                     as eh_conta_ativa
from {{ source('bronze', 'contas') }}
where num_conta is not null
  and saldo_total ~ '^-?[0-9]+\.?[0-9]*$'
