
    
    

select
    num_conta as unique_field,
    count(*) as n_records

from "banvic"."silver"."contas"
where num_conta is not null
group by num_conta
having count(*) > 1


