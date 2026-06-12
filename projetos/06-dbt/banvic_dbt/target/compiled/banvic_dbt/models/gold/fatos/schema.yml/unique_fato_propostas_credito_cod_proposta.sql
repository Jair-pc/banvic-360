
    
    

select
    cod_proposta as unique_field,
    count(*) as n_records

from "banvic"."gold"."fato_propostas_credito"
where cod_proposta is not null
group by cod_proposta
having count(*) > 1


