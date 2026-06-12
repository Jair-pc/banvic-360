
    
    

with all_values as (

    select
        canal as value_field,
        count(*) as n_records

    from "banvic"."silver"."transacoes"
    group by canal

)

select *
from all_values
where value_field not in (
    'Pix','TED','DOC','Compra Credito','Compra Debito','Saque','Deposito Especie','Pagamento Boleto','Outros'
)


