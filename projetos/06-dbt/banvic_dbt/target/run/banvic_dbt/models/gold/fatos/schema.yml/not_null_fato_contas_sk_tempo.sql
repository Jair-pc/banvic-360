select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select sk_tempo
from "banvic"."gold"."fato_contas"
where sk_tempo is null



      
    ) dbt_internal_test