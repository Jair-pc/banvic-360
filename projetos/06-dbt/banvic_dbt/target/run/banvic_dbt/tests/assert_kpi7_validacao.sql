select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      -- Teste singular: falha se KPI7 nao bater com o gabarito
-- Gabarito: 6 faixas, total clientes = 50997
-- Faixas: 18-24(5312), 25-34(12021), 35-44(16346), 45-54(11647), 55-64(4492), 65+(1179)

with resultado as (
    select
        count(*)             as qtd_faixas,
        sum(qtd_clientes)    as total_clientes
    from "banvic"."gold"."kpi7_segmentacao_clientes"
),
por_faixa as (
    select faixa_etaria, qtd_clientes
    from "banvic"."gold"."kpi7_segmentacao_clientes"
),
validacao_faixas as (
    select count(*) as faixas_erradas
    from (
        values
            ('18-24', 5312),
            ('25-34', 12021),
            ('35-44', 16346),
            ('45-54', 11647),
            ('55-64', 4492),
            ('65+',   1179)
    ) as esperado(faixa_etaria, qtd_esperada)
    left join por_faixa pf using (faixa_etaria)
    where coalesce(pf.qtd_clientes, 0) <> qtd_esperada
)
select r.*, v.*
from resultado r, validacao_faixas v
where r.qtd_faixas <> 6
   or r.total_clientes <> 50997
   or v.faixas_erradas > 0
      
    ) dbt_internal_test