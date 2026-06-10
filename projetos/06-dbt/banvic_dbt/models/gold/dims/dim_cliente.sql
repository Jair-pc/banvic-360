{{ config(materialized='table', schema='gold') }}

select
    row_number() over (order by cod_cliente)::integer   as sk_cliente,
    cod_cliente,
    primeiro_nome,
    ultimo_nome,
    cpf_formatado                                       as cpf,
    tipo_pessoa,
    email,
    data_nascimento,
    idade,
    faixa_etaria,
    cep_digits                                          as cep,
    cidade,
    uf,
    renda_mensal,
    faixa_renda,
    profissao,
    escolaridade,
    score_credito,
    faixa_score,
    data_inclusao,
    data_inclusao                                       as data_inicio_vigencia,
    '9999-12-31'::date                                  as data_fim_vigencia,
    true                                                as eh_registro_atual
from {{ ref('clientes') }}
