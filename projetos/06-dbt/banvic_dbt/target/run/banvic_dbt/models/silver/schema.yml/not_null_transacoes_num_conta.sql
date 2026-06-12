select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select num_conta
from "banvic"."silver"."transacoes"
where num_conta is null



      
    ) dbt_internal_test