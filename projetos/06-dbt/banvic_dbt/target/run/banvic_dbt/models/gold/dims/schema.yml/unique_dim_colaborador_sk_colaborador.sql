select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    sk_colaborador as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_colaborador"
where sk_colaborador is not null
group by sk_colaborador
having count(*) > 1



      
    ) dbt_internal_test