select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    sk_agencia as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_agencia"
where sk_agencia is not null
group by sk_agencia
having count(*) > 1



      
    ) dbt_internal_test