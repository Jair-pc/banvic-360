
    
    

with child as (
    select sk_agencia as from_field
    from "banvic"."gold"."fato_transacoes"
    where sk_agencia is not null
),

parent as (
    select sk_agencia as to_field
    from "banvic"."gold"."dim_agencia"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


