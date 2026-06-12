
    
    

select
    sk_colaborador as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_colaborador"
where sk_colaborador is not null
group by sk_colaborador
having count(*) > 1


