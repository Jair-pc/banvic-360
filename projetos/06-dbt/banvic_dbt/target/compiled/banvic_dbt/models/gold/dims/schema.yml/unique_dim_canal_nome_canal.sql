
    
    

select
    nome_canal as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_canal"
where nome_canal is not null
group by nome_canal
having count(*) > 1


