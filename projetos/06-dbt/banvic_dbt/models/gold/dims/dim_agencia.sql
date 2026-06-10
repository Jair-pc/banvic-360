{{ config(materialized='table', schema='gold') }}

select
    row_number() over (order by cod_agencia)::integer   as sk_agencia,
    cod_agencia,
    nome,
    tipo_agencia,
    cidade,
    uf,
    regiao,
    data_abertura,
    eh_ativa,
    meta_comercial_mensal,
    latitude,
    longitude
from {{ ref('agencias') }}
