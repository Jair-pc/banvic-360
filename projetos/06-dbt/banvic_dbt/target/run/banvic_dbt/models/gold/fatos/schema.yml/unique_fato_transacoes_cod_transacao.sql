select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    cod_transacao as unique_field,
    count(*) as n_records

from "banvic"."gold"."fato_transacoes"
where cod_transacao is not null
group by cod_transacao
having count(*) > 1



      
    ) dbt_internal_test