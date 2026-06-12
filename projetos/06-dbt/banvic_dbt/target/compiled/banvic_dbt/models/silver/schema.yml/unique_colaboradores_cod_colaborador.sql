
    
    

select
    cod_colaborador as unique_field,
    count(*) as n_records

from "banvic"."silver"."colaboradores"
where cod_colaborador is not null
group by cod_colaborador
having count(*) > 1


