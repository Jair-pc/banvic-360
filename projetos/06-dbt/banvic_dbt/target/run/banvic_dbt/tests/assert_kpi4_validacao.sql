select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      -- Teste singular: falha se KPI4 nao bater com o gabarito
-- Gabarito: 4 status, total propostas = 1996, min=468, max=525
-- Usa contagens em vez de nomes de status (evita problemas de encoding)

with resultado as (
    select
        count(*)             as qtd_status,
        sum(qtd_propostas)   as total_propostas,
        min(qtd_propostas)   as min_qtd,
        max(qtd_propostas)   as max_qtd
    from "banvic"."gold"."kpi4_conversao_propostas"
)
select *
from resultado
where qtd_status <> 4
   or total_propostas <> 1996
   or min_qtd <> 468
   or max_qtd <> 525
      
    ) dbt_internal_test