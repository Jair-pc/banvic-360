select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select sk_canal
from "banvic"."gold"."dim_canal"
where sk_canal is null



      
    ) dbt_internal_test