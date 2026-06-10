{{ config(materialized='table', schema='silver') }}

with expandidos as (
    select
        e.cod_colaborador::integer      as cod_colaborador,
        e.primeiro_nome, e.ultimo_nome,
        lower(e.email)                  as email,
        e.cpf,
        e.data_nascimento::date         as data_nascimento,
        e.cidade, upper(e.uf) as uf, e.regiao,
        e.cargo,
        e.nivel_hierarquico::smallint   as nivel_hierarquico,
        e.departamento,
        e.salario_base::numeric(12,2)   as salario_base,
        e.cod_agencia::integer          as cod_agencia,
        e.data_admissao::date           as data_admissao,
        nullif(e.data_demissao, '')::date as data_demissao,
        e.eh_ativo::boolean             as eh_ativo
    from {{ source('bronze', 'colaboradores_expandidos') }} e
    where e.cod_colaborador is not null
),

originais_nao_expandidos as (
    select
        c.cod_colaborador::integer,
        c.primeiro_nome, c.ultimo_nome,
        lower(c.email), c.cpf,
        c.data_nascimento::date,
        null::text, null::text, null::text,
        c.cargo,
        null::smallint, null::text, null::numeric(12,2),
        null::integer, null::date, null::date, true::boolean
    from {{ source('bronze', 'colaboradores') }} c
    where not exists (
        select 1 from {{ source('bronze', 'colaboradores_expandidos') }} e
        where e.cod_colaborador = c.cod_colaborador
    )
)

select * from expandidos
union all
select * from originais_nao_expandidos
