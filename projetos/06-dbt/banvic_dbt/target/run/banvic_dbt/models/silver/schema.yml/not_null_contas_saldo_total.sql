select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select saldo_total
from "banvic"."silver"."contas"
where saldo_total is null



      
    ) dbt_internal_test