select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      -- Teste singular: falha se KPI8 nao bater com o gabarito
-- Gabarito: 155 meses, volume_nominal total = 58122708.67

with resultado as (
    select
        count(*)                                    as qtd_meses,
        round(sum(volume_nominal)::numeric, 2)      as total_volume_nominal
    from "banvic"."gold"."kpi8_correcao_ipca"
)
select *
from resultado
where qtd_meses <> 155
   or abs(total_volume_nominal - 58122708.67) > 0.10
      
    ) dbt_internal_test