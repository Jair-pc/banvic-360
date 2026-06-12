select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select data
from "banvic"."gold"."dim_tempo"
where data is null



      
    ) dbt_internal_test