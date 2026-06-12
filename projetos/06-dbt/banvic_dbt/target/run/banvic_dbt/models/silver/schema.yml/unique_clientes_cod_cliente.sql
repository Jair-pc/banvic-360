select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    cod_cliente as unique_field,
    count(*) as n_records

from "banvic"."silver"."clientes"
where cod_cliente is not null
group by cod_cliente
having count(*) > 1



      
    ) dbt_internal_test