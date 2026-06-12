-- Teste singular: falha se KPI6 nao bater com o gabarito
-- Gabarito: 100 colaboradores ativos, saldo_gerido total = 26509620.12

with resultado as (
    select
        count(*)                                    as qtd_colaboradores,
        round(sum(saldo_gerido)::numeric, 2)        as total_saldo_gerido
    from {{ ref('kpi6_carteira_colaborador') }}
)
select *
from resultado
where qtd_colaboradores <> 100
   or abs(total_saldo_gerido - 26509620.12) > 0.10
