select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    cod_agencia as unique_field,
    count(*) as n_records

from "banvic"."silver"."agencias"
where cod_agencia is not null
group by cod_agencia
having count(*) > 1



      
    ) dbt_internal_test