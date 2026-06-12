

select
    row_number() over (order by c.cod_colaborador)::integer     as sk_colaborador,
    c.cod_colaborador,
    c.primeiro_nome,
    c.ultimo_nome,
    c.cpf,
    c.email,
    c.data_nascimento,
    c.cargo,
    c.departamento,
    c.nivel_hierarquico,
    c.salario_base,
    c.data_admissao,
    c.data_demissao,
    c.eh_ativo,
    a.sk_agencia                                                 as sk_agencia_principal,
    c.cidade,
    c.uf
from "banvic"."silver"."colaboradores" c
left join "banvic"."gold"."dim_agencia" a on a.cod_agencia = c.cod_agencia