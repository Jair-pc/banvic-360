select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select valor_transacao
from "banvic"."silver"."transacoes"
where valor_transacao is null



      
    ) dbt_internal_test