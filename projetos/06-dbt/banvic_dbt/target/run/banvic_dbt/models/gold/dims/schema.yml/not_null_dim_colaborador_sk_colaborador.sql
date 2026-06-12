select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select sk_colaborador
from "banvic"."gold"."dim_colaborador"
where sk_colaborador is null



      
    ) dbt_internal_test