
    
    

select
    sk_canal as unique_field,
    count(*) as n_records

from "banvic"."gold"."dim_canal"
where sk_canal is not null
group by sk_canal
having count(*) > 1


