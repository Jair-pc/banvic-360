select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      -- Teste singular: falha se KPI5 nao bater com o gabarito
-- Gabarito: 10 agencias, saldo total = 26509620.12, volume total = 58122708.67, top = agencia 7

with resultado as (
    select
        count(*)                                    as qtd_agencias,
        round(sum(saldo_total)::numeric, 2)         as total_saldo,
        round(sum(volume_total)::numeric, 2)        as total_volume
    from "banvic"."gold"."kpi5_ranking_agencias"
),
top1 as (
    select cod_agencia::text as top_agencia
    from "banvic"."gold"."kpi5_ranking_agencias"
    where ranking = 1
)
select r.*, t.*
from resultado r, top1 t
where r.qtd_agencias <> 10
   or abs(r.total_saldo - 26509620.12) > 0.10
   or abs(r.total_volume - 58122708.67) > 0.10
   or t.top_agencia <> '7'
      
    ) dbt_internal_test