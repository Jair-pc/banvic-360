select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select nome_canal
from "banvic"."gold"."dim_canal"
where nome_canal is null



      
    ) dbt_internal_test