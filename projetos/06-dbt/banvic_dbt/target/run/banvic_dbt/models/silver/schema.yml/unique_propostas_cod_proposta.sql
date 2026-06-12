select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    cod_proposta as unique_field,
    count(*) as n_records

from "banvic"."silver"."propostas"
where cod_proposta is not null
group by cod_proposta
having count(*) > 1



      
    ) dbt_internal_test