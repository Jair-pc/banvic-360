select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cod_cliente
from "banvic"."silver"."contas"
where cod_cliente is null



      
    ) dbt_internal_test