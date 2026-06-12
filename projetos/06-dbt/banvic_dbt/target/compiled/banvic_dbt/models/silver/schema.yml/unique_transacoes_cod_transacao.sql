
    
    

select
    cod_transacao as unique_field,
    count(*) as n_records

from "banvic"."silver"."transacoes"
where cod_transacao is not null
group by cod_transacao
having count(*) > 1


