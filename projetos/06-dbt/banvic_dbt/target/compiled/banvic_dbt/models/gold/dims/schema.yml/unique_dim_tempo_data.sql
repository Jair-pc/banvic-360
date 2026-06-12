
    
    

select
    data as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_tempo"
where data is not null
group by data
having count(*) > 1


