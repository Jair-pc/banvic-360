
    
    

select
    cod_agencia as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_agencia"
where cod_agencia is not null
group by cod_agencia
having count(*) > 1


