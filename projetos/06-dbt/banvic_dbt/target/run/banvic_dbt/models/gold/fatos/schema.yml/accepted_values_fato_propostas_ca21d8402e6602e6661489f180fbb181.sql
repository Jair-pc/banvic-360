
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with all_values as (

    select
        status_proposta as value_field,
        count(*) as n_records

    from "banvic"."gold"."fato_propostas_credito"
    group by status_proposta

)

select *
from all_values
where value_field not in (
    'Aprovada','Reprovada','Enviada','Em Analise','Cancelada'
)



  
  
      
    ) dbt_internal_test