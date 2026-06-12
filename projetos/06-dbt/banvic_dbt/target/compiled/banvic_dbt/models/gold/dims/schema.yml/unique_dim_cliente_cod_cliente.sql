
    
    

select
    cod_cliente as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_cliente"
where cod_cliente is not null
group by cod_cliente
having count(*) > 1


