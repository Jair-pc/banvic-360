select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cod_proposta
from "banvic"."gold"."fato_propostas_credito"
where cod_proposta is null



      
    ) dbt_internal_test