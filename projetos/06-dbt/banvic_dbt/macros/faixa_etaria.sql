{% macro faixa_etaria(idade_col) %}
    CASE
        WHEN {{ idade_col }} BETWEEN 18 AND 24 THEN '18-24'
        WHEN {{ idade_col }} BETWEEN 25 AND 34 THEN '25-34'
        WHEN {{ idade_col }} BETWEEN 35 AND 44 THEN '35-44'
        WHEN {{ idade_col }} BETWEEN 45 AND 54 THEN '45-54'
        WHEN {{ idade_col }} BETWEEN 55 AND 64 THEN '55-64'
        WHEN {{ idade_col }} >= 65             THEN '65+'
        ELSE 'Menor'
    END
{% endmacro %}
