
  
    

  create  table "banvic"."gold"."fato_contas__dbt_tmp"
  
  
    as
  
  (
    

-- Grain: 1 linha por conta (snapshot corrente)
-- sk_tempo aponta para a data do ultimo lancamento

select
    t.sk_tempo,
    cli.sk_cliente,
    ag.sk_agencia,
    col.sk_colaborador,
    c.num_conta,
    c.saldo_total,
    c.saldo_disponivel,
    true    as eh_conta_ativa
from "banvic"."silver"."contas" c
join "banvic"."gold"."dim_tempo" t
    on t.data = coalesce(c.data_ultimo_lancamento, current_date)
join "banvic"."gold"."dim_cliente" cli
    on cli.cod_cliente = c.cod_cliente
   and cli.eh_registro_atual = true
join "banvic"."gold"."dim_agencia" ag
    on ag.cod_agencia = c.cod_agencia
left join "banvic"."gold"."dim_colaborador" col
    on col.cod_colaborador = c.cod_colaborador
  );
  