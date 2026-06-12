select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select cod_colaborador
from "banvic"."silver"."colaboradores"
where cod_colaborador is null



      
    ) dbt_internal_test