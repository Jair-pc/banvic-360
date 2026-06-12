select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cod_transacao
from "banvic"."silver"."transacoes"
where cod_transacao is null



      
    ) dbt_internal_test