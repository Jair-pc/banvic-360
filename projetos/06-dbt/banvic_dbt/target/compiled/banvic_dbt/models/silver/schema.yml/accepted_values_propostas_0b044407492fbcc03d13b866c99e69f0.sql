
    
    

with all_values as (

    select
        status_proposta as value_field,
        count(*) as n_records

    from "banvic"."silver"."propostas"
    group by status_proposta

)

select *
from all_values
where value_field not in (
    'Aprovada','Reprovada','Enviada','Em Analise','Cancelada'
)


