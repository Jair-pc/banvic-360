

with source as (
    select * from "banvic"."bronze"."clientes"
    where cod_cliente is not null and cpfcnpj is not null
),
sinteticos as (
    select * from "banvic"."bronze"."clientes_sinteticos"
    where cod_cliente is not null
),

reais_tratados as (
    select
        cod_cliente::integer                                     as cod_cliente,
        trim(primeiro_nome)                                      as primeiro_nome,
        trim(ultimo_nome)                                        as ultimo_nome,
        lower(trim(email))                                       as email,
        upper(trim(tipo_cliente))                                as tipo_pessoa,
        data_inclusao::date                                      as data_inclusao,
        regexp_replace(cpfcnpj, '[^0-9]', '', 'g')              as cpf_digits,
        cpfcnpj                                                  as cpf_formatado,
        data_nascimento::date                                    as data_nascimento,
        extract(year from age('2026-06-10'::date, data_nascimento::date))::smallint as idade,
        
    CASE
        WHEN extract(year from age('2026-06-10'::date, data_nascimento::date)) BETWEEN 18 AND 24 THEN '18-24'
        WHEN extract(year from age('2026-06-10'::date, data_nascimento::date)) BETWEEN 25 AND 34 THEN '25-34'
        WHEN extract(year from age('2026-06-10'::date, data_nascimento::date)) BETWEEN 35 AND 44 THEN '35-44'
        WHEN extract(year from age('2026-06-10'::date, data_nascimento::date)) BETWEEN 45 AND 54 THEN '45-54'
        WHEN extract(year from age('2026-06-10'::date, data_nascimento::date)) BETWEEN 55 AND 64 THEN '55-64'
        WHEN extract(year from age('2026-06-10'::date, data_nascimento::date)) >= 65             THEN '65+'
        ELSE 'Menor'
    END
 as faixa_etaria,
        trim(endereco)                                           as endereco,
        regexp_replace(cep, '[^0-9]', '', 'g')                  as cep_digits,
        null::text                                               as cidade,
        null::text                                               as uf,
        null::numeric                                            as renda_mensal,
        null::text                                               as faixa_renda,
        null::text                                               as profissao,
        null::text                                               as escolaridade,
        null::smallint                                           as score_credito,
        null::text                                               as faixa_score
    from source
),

sinteticos_tratados as (
    select
        cod_cliente::integer                   as cod_cliente,
        trim(primeiro_nome)                    as primeiro_nome,
        trim(ultimo_nome)                      as ultimo_nome,
        lower(trim(email))                     as email,
        upper(tipo_cliente)                    as tipo_pessoa,
        data_inclusao::date                    as data_inclusao,
        cpfcnpj                                as cpf_digits,
        cpfcnpj                                as cpf_formatado,
        data_nascimento::date                  as data_nascimento,
        idade::smallint                        as idade,
        faixa_etaria,
        null::text                             as endereco,
        cep                                    as cep_digits,
        cidade,
        upper(uf)                              as uf,
        renda_mensal::numeric                  as renda_mensal,
        faixa_renda,
        profissao,
        escolaridade,
        score_credito::smallint                as score_credito,
        faixa_score
    from sinteticos
),

todos as (
    select * from reais_tratados
    union all
    select * from sinteticos_tratados
),

deduplicados as (
    select *,
        row_number() over (partition by cod_cliente order by data_inclusao desc) as _rn
    from todos
)

select
    cod_cliente, primeiro_nome, ultimo_nome, email,
    tipo_pessoa, data_inclusao, cpf_digits, cpf_formatado,
    data_nascimento, idade, faixa_etaria, endereco, cep_digits,
    cidade, uf, renda_mensal, faixa_renda, profissao, escolaridade,
    score_credito, faixa_score
from deduplicados
where _rn = 1