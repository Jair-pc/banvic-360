
  create view "banvic"."gold"."kpi2_3_transacoes__dbt_tmp"
    
    
  as (
    

select
    t.ano,
    t.mes,
    t.mes_nome,
    ft.nome_transacao,
    count(*)                                                                                    as qtd_transacoes,
    round(sum(abs(ft.valor_transacao))::numeric, 2)                                            as volume,
    round(count(*) * 100.0 / sum(count(*)) over (partition by t.ano, t.mes), 2)               as pct_mix,
    cast(t.ano || '-' || lpad(t.mes::text, 2, '0') as text)                                   as ano_mes
from "banvic"."gold"."fato_transacoes" ft
join "banvic"."gold"."dim_tempo" t on t.sk_tempo = ft.sk_tempo
group by t.ano, t.mes, t.mes_nome, ft.nome_transacao
order by t.ano, t.mes, volume desc
  );