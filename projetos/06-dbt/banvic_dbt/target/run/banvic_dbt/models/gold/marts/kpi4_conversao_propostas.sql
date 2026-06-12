
  create view "banvic"."gold"."kpi4_conversao_propostas__dbt_tmp"
    
    
  as (
    

select
    status_proposta,
    count(*)                            as qtd_propostas,
    round(avg(valor_proposta), 2)       as valor_medio_proposta,
    round(sum(valor_proposta), 2)       as valor_total_proposta
from "banvic"."gold"."fato_propostas_credito"
group by status_proposta
order by qtd_propostas desc
  );