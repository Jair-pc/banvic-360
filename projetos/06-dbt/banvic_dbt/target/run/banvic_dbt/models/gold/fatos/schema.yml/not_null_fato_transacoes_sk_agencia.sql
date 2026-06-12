select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select sk_agencia
from "banvic"."gold"."fato_transacoes"
where sk_agencia is null



      
    ) dbt_internal_test