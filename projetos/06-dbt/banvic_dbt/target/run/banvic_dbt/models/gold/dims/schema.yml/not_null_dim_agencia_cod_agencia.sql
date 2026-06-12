select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cod_agencia
from "banvic"."gold"."dim_agencia"
where cod_agencia is null



      
    ) dbt_internal_test