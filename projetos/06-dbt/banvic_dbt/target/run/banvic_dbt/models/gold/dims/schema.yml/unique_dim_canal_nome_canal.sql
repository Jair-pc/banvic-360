select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    nome_canal as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_canal"
where nome_canal is not null
group by nome_canal
having count(*) > 1



      
    ) dbt_internal_test