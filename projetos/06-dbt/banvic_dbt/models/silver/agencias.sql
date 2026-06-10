{{ config(materialized='table', schema='silver') }}

select
    a.cod_agencia::integer              as cod_agencia,
    trim(a.nome)                        as nome,
    upper(trim(a.tipo_agencia))         as tipo_agencia,
    a.cidade,
    upper(a.uf)                         as uf,
    case upper(a.uf)
        when 'SP' then 'Sudeste' when 'RJ' then 'Sudeste'
        when 'MG' then 'Sudeste' when 'ES' then 'Sudeste'
        when 'RS' then 'Sul'     when 'SC' then 'Sul'     when 'PR' then 'Sul'
        when 'BA' then 'Nordeste' when 'PE' then 'Nordeste'
        when 'CE' then 'Nordeste' when 'MA' then 'Nordeste'
        when 'PB' then 'Nordeste' when 'RN' then 'Nordeste'
        when 'AL' then 'Nordeste' when 'SE' then 'Nordeste' when 'PI' then 'Nordeste'
        when 'GO' then 'Centro-Oeste' when 'MT' then 'Centro-Oeste'
        when 'MS' then 'Centro-Oeste' when 'DF' then 'Centro-Oeste'
        when 'AM' then 'Norte' when 'PA' then 'Norte' when 'AC' then 'Norte'
        when 'RO' then 'Norte' when 'RR' then 'Norte' when 'AP' then 'Norte'
        when 'TO' then 'Norte'
        else 'Sudeste'
    end                                 as regiao,
    a.data_abertura::date               as data_abertura,
    coalesce(e.meta_comercial_mensal::numeric, 500000) as meta_comercial_mensal,
    coalesce(e.latitude::numeric, null)    as latitude,
    coalesce(e.longitude::numeric, null)   as longitude,
    true                                   as eh_ativa
from {{ source('bronze', 'agencias') }} a
left join {{ source('bronze', 'agencias_expandidas') }} e
       on e.cod_agencia = a.cod_agencia
where a.cod_agencia is not null
