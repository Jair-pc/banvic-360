
    
    

select
    cod_proposta as unique_field,
    count(*) as n_records

from "banvic"."silver"."propostas"
where cod_proposta is not null
group by cod_proposta
having count(*) > 1


