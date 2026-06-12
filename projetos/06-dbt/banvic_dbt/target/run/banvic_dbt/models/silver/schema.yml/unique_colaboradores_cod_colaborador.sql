select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    cod_colaborador as unique_field,
    count(*) as n_records

from "banvic"."silver"."colaboradores"
where cod_colaborador is not null
group by cod_colaborador
having count(*) > 1



      
    ) dbt_internal_test