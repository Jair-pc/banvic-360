select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        faixa_etaria as value_field,
        count(*) as n_records

    from "banvic"."gold"."dim_cliente"
    group by faixa_etaria

)

select *
from all_values
where value_field not in (
    '18-24','25-34','35-44','45-54','55-64','65+','Menor'
)



      
    ) dbt_internal_test