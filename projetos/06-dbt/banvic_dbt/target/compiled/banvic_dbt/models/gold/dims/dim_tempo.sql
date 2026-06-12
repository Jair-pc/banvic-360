

with dates as (
    select generate_series(
        '2010-01-01'::date,
        '2026-12-31'::date,
        '1 day'::interval
    )::date as data
),

base as (
    select
        data,
        extract(year    from data)::smallint                    as ano,
        case when extract(month from data) <= 6 then 1 else 2 end::smallint as semestre,
        extract(quarter from data)::smallint                    as trimestre,
        extract(month   from data)::smallint                    as mes,
        to_char(data, 'TMMonth')                                as mes_nome,
        upper(substring(to_char(data, 'TMMonth'), 1, 3))        as mes_abrev,
        extract(week    from data)::smallint                    as semana_ano,
        extract(day     from data)::smallint                    as dia_mes,
        extract(dow     from data)::smallint                    as dia_semana,
        to_char(data, 'TMDay')                                  as dia_semana_nome,
        upper(substring(to_char(data, 'TMDay'), 1, 3))          as dia_semana_abrev,
        extract(dow from data) in (0, 6)                        as eh_fim_semana,
        case when extract(dow from data) in (0, 6) then false else true end as eh_dia_util
    from dates
),

enriched as (
    select
        b.*,
        s.taxa_selic::numeric               as taxa_selic,
        cd.taxa_cdi::numeric                as taxa_cdi,
        p.cotacao_media::numeric            as cotacao_dolar,
        e.cotacao_media::numeric            as cotacao_euro,
        i.no_mes::numeric                   as ipca_mes,
        i.acumulado_12m::numeric            as ipca_acum_12m,
        i.indice::numeric                   as indice_ipca,
        case when f.data is not null then true else false end    as eh_feriado,
        f.nome                              as nome_feriado,
        f.tipo                              as tipo_feriado,
        case when extract(dow from b.data) in (0, 6)
              or f.data is not null then false else true end     as eh_dia_util_final
    from base b
    left join "banvic"."bronze"."selic" s
           on b.data = s.data::date
          and s.taxa_selic ~ '^-?[0-9]+\.?[0-9]*$'
    left join "banvic"."bronze"."cdi" cd
           on b.data = cd.data::date
          and cd.taxa_cdi ~ '^-?[0-9]+\.?[0-9]*$'
    left join "banvic"."bronze"."dolar_ptax" p
           on b.data = p.data::date
          and p.cotacao_media ~ '^-?[0-9]+\.?[0-9]*$'
    left join "banvic"."bronze"."euro_ptax" e
           on b.data = e.data::date
          and e.cotacao_media ~ '^-?[0-9]+\.?[0-9]*$'
    left join "banvic"."bronze"."ipca" i
           on b.ano  = i.ano::smallint
          and b.mes  = i.mes_num::smallint
          and i.indice ~ '^-?[0-9]+\.?[0-9]*$'
    left join "banvic"."bronze"."feriados" f
           on b.data = f.data::date
)

select
    row_number() over (order by data)::integer  as sk_tempo,
    data, ano, semestre, trimestre, mes, mes_nome, mes_abrev,
    semana_ano, dia_mes, dia_semana, dia_semana_nome, dia_semana_abrev,
    eh_fim_semana,
    eh_feriado, nome_feriado, tipo_feriado,
    coalesce(eh_dia_util_final, eh_dia_util)     as eh_dia_util,
    taxa_selic, taxa_cdi, cotacao_dolar, cotacao_euro,
    ipca_mes, ipca_acum_12m, indice_ipca
from enriched