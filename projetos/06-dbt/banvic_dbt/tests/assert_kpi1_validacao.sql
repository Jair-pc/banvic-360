-- Teste singular: falha se KPI1 nao bater com o gabarito
-- Gabarito: 10 agencias, saldo total = R$ 26.509.620,12
-- Retorna linhas em caso de falha — dbt considera isso como test failure

with resultado as (
    select
        count(*)                            as qtd_agencias,
        round(sum(saldo_total)::numeric, 2) as total_saldo
    from {{ ref('kpi1_saldo_agencia') }}
)
select *
from resultado
where qtd_agencias <> 10
   or abs(total_saldo - 26509620.12) > 0.10
