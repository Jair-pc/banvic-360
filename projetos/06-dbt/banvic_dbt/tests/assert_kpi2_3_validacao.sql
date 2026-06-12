-- Teste singular: falha se KPI2/3 nao bater com o gabarito
-- Gabarito: 1478 linhas (mes/tipo), volume total = R$ 58.122.708,67

with resultado as (
    select
        count(*)                                    as qtd_linhas,
        round(sum(volume)::numeric, 2)              as total_volume
    from {{ ref('kpi2_3_transacoes') }}
)
select *
from resultado
where qtd_linhas <> 1478
   or abs(total_volume - 58122708.67) > 0.10
