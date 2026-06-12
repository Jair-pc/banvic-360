
  create view "banvic"."gold"."kpi8_correcao_ipca__dbt_tmp"
    
    
  as (
    

with base_ipca as (
    select indice_ipca
    from "banvic"."gold"."dim_tempo"
    where data = (
        select max(data) from "banvic"."gold"."dim_tempo" where indice_ipca is not null
    )
    limit 1
)
select
    t.ano,
    t.mes,
    t.mes_nome,
    t.indice_ipca                                                                             as indice_mes,
    b.indice_ipca                                                                             as indice_base,
    round(sum(abs(ft.valor_transacao))::numeric, 2)                                          as volume_nominal,
    round((sum(abs(ft.valor_transacao)) * b.indice_ipca / nullif(t.indice_ipca, 0))::numeric, 2) as volume_real,
    cast(t.ano || '-' || lpad(t.mes::text, 2, '0') as text)                                 as ano_mes
from "banvic"."gold"."fato_transacoes" ft
join "banvic"."gold"."dim_tempo" t on t.sk_tempo = ft.sk_tempo
cross join base_ipca b
where t.indice_ipca is not null
group by t.ano, t.mes, t.mes_nome, t.indice_ipca, b.indice_ipca
order by t.ano, t.mes
  );