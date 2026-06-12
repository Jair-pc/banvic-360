
    
    

select
    cod_colaborador as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_colaborador"
where cod_colaborador is not null
group by cod_colaborador
having count(*) > 1


