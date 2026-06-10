-- ================================================================
-- BanVic 360° — Framework de Qualidade de Dados (DQ)
-- ================================================================
-- Executar após carga do Bronze para auditar antes de promover para Silver.
-- Cada bloco retorna um "scorecard" de qualidade por tabela.
-- ================================================================

-- ── SCHEMA DE AUDITORIA ──────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS dq;

-- Tabela de registro de erros de qualidade
CREATE TABLE IF NOT EXISTS dq.audit_log (
    id              BIGSERIAL   PRIMARY KEY,
    ts_execucao     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    tabela          TEXT        NOT NULL,
    campo           TEXT,
    regra           TEXT        NOT NULL,
    severidade      TEXT        NOT NULL,  -- ERROR, WARNING, INFO
    qtd_registros   INTEGER     DEFAULT 0,
    amostra         TEXT,                  -- JSON com exemplos
    status          TEXT        DEFAULT 'ABERTO'  -- ABERTO, RESOLVIDO
);

-- ================================================================
-- 1. CLIENTES — Regras de qualidade
-- ================================================================

-- 1.1 CPF com formato inválido (deveria ser XXX.XXX.XXX-XX)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros, amostra)
SELECT
    'clientes', 'cpfcnpj', 'Formato CPF inválido (não segue XXX.XXX.XXX-XX)', 'ERROR',
    COUNT(*),
    (SELECT ARRAY_TO_STRING(ARRAY_AGG(s), ' | ')
     FROM (SELECT cpfcnpj AS s FROM bronze.clientes
           WHERE cpfcnpj IS NOT NULL AND cpfcnpj !~ '^\d{3}\.\d{3}\.\d{3}-\d{2}$'
           ORDER BY cpfcnpj LIMIT 5) _sub)
FROM bronze.clientes
WHERE cpfcnpj IS NOT NULL
  AND cpfcnpj !~ '^\d{3}\.\d{3}\.\d{3}-\d{2}$';

-- 1.2 CPFs duplicados
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros, amostra)
SELECT
    'clientes', 'cpfcnpj', 'CPF duplicado', 'ERROR',
    COUNT(*) - COUNT(DISTINCT cpfcnpj),
    ARRAY_TO_STRING(
        ARRAY(SELECT cpfcnpj FROM bronze.clientes
              GROUP BY cpfcnpj HAVING COUNT(*) > 1 LIMIT 5), ' | ')
FROM bronze.clientes
WHERE cpfcnpj IS NOT NULL
HAVING COUNT(*) - COUNT(DISTINCT cpfcnpj) > 0;

-- 1.3 Email duplicado
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'clientes', 'email', 'Email duplicado', 'WARNING', COUNT(*) - COUNT(DISTINCT LOWER(email))
FROM bronze.clientes
WHERE email IS NOT NULL
HAVING COUNT(*) - COUNT(DISTINCT LOWER(email)) > 0;

-- 1.4 Data de nascimento inválida (menor de 18 anos ou maior de 120)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'clientes', 'data_nascimento', 'Idade fora do range 18-120 anos', 'ERROR',
    COUNT(*)
FROM bronze.clientes
WHERE data_nascimento IS NOT NULL
  AND (
    EXTRACT(YEAR FROM AGE(data_nascimento::DATE)) < 18
    OR EXTRACT(YEAR FROM AGE(data_nascimento::DATE)) > 120
  );

-- 1.5 Clientes sem email
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'clientes', 'email', 'Email nulo', 'WARNING', COUNT(*)
FROM bronze.clientes WHERE email IS NULL OR email = '';

-- ================================================================
-- 2. CONTAS — Regras de qualidade
-- ================================================================

-- 2.1 Contas sem cliente correspondente (integridade referencial)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'contas', 'cod_cliente', 'Conta sem cliente correspondente', 'ERROR',
    COUNT(*)
FROM bronze.contas c
LEFT JOIN bronze.clientes cl ON cl.cod_cliente = c.cod_cliente
WHERE cl.cod_cliente IS NULL;

-- 2.2 Contas sem agência correspondente
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'contas', 'cod_agencia', 'Conta sem agência correspondente', 'ERROR',
    COUNT(*)
FROM bronze.contas c
LEFT JOIN bronze.agencias a ON a.cod_agencia = c.cod_agencia
WHERE a.cod_agencia IS NULL;

-- 2.3 Saldo disponível maior que saldo total (inconsistência)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros, amostra)
SELECT 'contas', 'saldo_disponivel',
    'Saldo disponível > saldo total (inconsistência)', 'ERROR',
    COUNT(*),
    (SELECT ARRAY_TO_STRING(ARRAY_AGG(s), ' | ')
     FROM (SELECT num_conta::TEXT AS s FROM bronze.contas
           WHERE saldo_disponivel::NUMERIC > saldo_total::NUMERIC + 0.01
           LIMIT 5) _sub)
FROM bronze.contas
WHERE saldo_disponivel::NUMERIC > saldo_total::NUMERIC + 0.01;  -- tolerancia de centavo

-- 2.4 Contas com data de abertura futura
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'contas', 'data_abertura', 'Data de abertura no futuro', 'ERROR', COUNT(*)
FROM bronze.contas
WHERE data_abertura::DATE > CURRENT_DATE;

-- ================================================================
-- 3. TRANSAÇÕES — Regras de qualidade
-- ================================================================

-- 3.1 Transações com valor zero
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'transacoes', 'valor_transacao', 'Valor de transação = 0', 'ERROR', COUNT(*)
FROM bronze.transacoes WHERE valor_transacao::NUMERIC = 0;

-- 3.2 Transações para conta inexistente
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'transacoes', 'num_conta', 'Transação sem conta correspondente', 'ERROR',
    COUNT(DISTINCT t.num_conta)
FROM bronze.transacoes t
LEFT JOIN bronze.contas c ON c.num_conta = t.num_conta
WHERE c.num_conta IS NULL;

-- 3.3 Transações com data anterior à abertura da conta
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'transacoes', 'data_transacao',
    'Data da transação anterior à abertura da conta', 'ERROR',
    COUNT(*)
FROM bronze.transacoes t
JOIN bronze.contas c ON c.num_conta = t.num_conta
WHERE t.data_transacao::DATE < c.data_abertura::DATE;

-- 3.4 Transações com valor muito alto (outlier > R$1M)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'transacoes', 'valor_transacao', 'Valor transação > R$1.000.000 (outlier)', 'WARNING',
    COUNT(*)
FROM bronze.transacoes WHERE ABS(valor_transacao::NUMERIC) > 1000000;

-- ================================================================
-- 4. PROPOSTAS — Regras de qualidade
-- ================================================================

-- 4.1 Taxa de juros fora do range esperado (0% a 30% a.m.)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'propostas_credito', 'taxa_juros_mensal',
    'Taxa de juros fora do range 0%-30% a.m.', 'ERROR',
    COUNT(*)
FROM bronze.propostas_credito
WHERE taxa_juros_mensal::NUMERIC NOT BETWEEN 0 AND 0.30;

-- 4.2 Valor de entrada maior que valor da proposta
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'propostas_credito', 'valor_entrada',
    'Valor de entrada ≥ valor da proposta (sem sentido financeiro)', 'ERROR',
    COUNT(*)
FROM bronze.propostas_credito
WHERE valor_entrada::NUMERIC >= valor_proposta::NUMERIC;

-- 4.3 Propostas sem cliente correspondente
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'propostas_credito', 'cod_cliente',
    'Proposta sem cliente correspondente', 'ERROR',
    COUNT(*)
FROM bronze.propostas_credito p
LEFT JOIN bronze.clientes c ON c.cod_cliente = p.cod_cliente
WHERE c.cod_cliente IS NULL;

-- ================================================================
-- 5. INDICADORES ECONÔMICOS — Regras de qualidade
-- ================================================================

-- 5.1 Gaps na série do IPCA (meses faltando)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
WITH meses_esperados AS (
    SELECT generate_series(
        '2010-01-01'::DATE,
        '2025-12-01'::DATE,
        '1 month'
    )::DATE AS data_esperada
),
meses_presentes AS (
    SELECT DATE_TRUNC('month', data::DATE)::DATE AS data_presente
    FROM bronze.ipca
)
SELECT 'ipca', 'data', 'Mês faltando na série IPCA', 'ERROR',
    COUNT(*)
FROM meses_esperados m
LEFT JOIN meses_presentes p ON p.data_presente = m.data_esperada
WHERE p.data_presente IS NULL;

-- 5.2 Selic com gaps em dias úteis
-- (simplificado: verifica se há mais de 5 dias consecutivos sem dados)
INSERT INTO dq.audit_log (tabela, campo, regra, severidade, qtd_registros)
SELECT 'selic', 'data', 'Possível gap na série Selic (verificar manualmente)', 'WARNING',
    0;  -- placeholder — análise manual de gaps em dias úteis

-- ================================================================
-- 6. SCORECARD CONSOLIDADO
-- ================================================================

CREATE OR REPLACE VIEW dq.scorecard AS
SELECT
    tabela,
    severidade,
    COUNT(*)                AS qtd_regras_violadas,
    SUM(qtd_registros)      AS total_registros_afetados,
    SUM(CASE WHEN status = 'ABERTO' THEN qtd_registros ELSE 0 END)
                            AS registros_em_aberto
FROM dq.audit_log
GROUP BY tabela, severidade
ORDER BY tabela,
    CASE severidade WHEN 'ERROR' THEN 1 WHEN 'WARNING' THEN 2 ELSE 3 END;

-- Executar para ver o scorecard:
-- SELECT * FROM dq.scorecard;

-- ================================================================
-- 7. FUNÇÕES DE VALIDAÇÃO REUTILIZÁVEIS
-- ================================================================

-- Validar dígitos verificadores do CPF
CREATE OR REPLACE FUNCTION dq.valida_cpf(cpf TEXT) RETURNS BOOLEAN AS $$
DECLARE
    digitos TEXT;
    soma1 INT := 0;
    soma2 INT := 0;
    d1 INT;
    d2 INT;
BEGIN
    digitos := REGEXP_REPLACE(cpf, '[^0-9]', '', 'g');
    IF LENGTH(digitos) != 11 THEN RETURN FALSE; END IF;
    IF digitos = REPEAT(SUBSTRING(digitos, 1, 1), 11) THEN RETURN FALSE; END IF;

    FOR i IN 1..9 LOOP
        soma1 := soma1 + SUBSTRING(digitos, i, 1)::INT * (11 - i);
    END LOOP;
    d1 := CASE WHEN (11 - soma1 % 11) >= 10 THEN 0 ELSE 11 - soma1 % 11 END;

    FOR i IN 1..10 LOOP
        soma2 := soma2 + SUBSTRING(digitos, i, 1)::INT * (12 - i);
    END LOOP;
    d2 := CASE WHEN (11 - soma2 % 11) >= 10 THEN 0 ELSE 11 - soma2 % 11 END;

    RETURN d1 = SUBSTRING(digitos, 10, 1)::INT
       AND d2 = SUBSTRING(digitos, 11, 1)::INT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Uso: SELECT cpfcnpj, dq.valida_cpf(cpfcnpj) FROM bronze.clientes;

-- Validar formato de CEP
CREATE OR REPLACE FUNCTION dq.valida_cep(cep TEXT) RETURNS BOOLEAN AS $$
BEGIN
    RETURN REGEXP_REPLACE(cep, '[^0-9]', '', 'g') ~ '^\d{8}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Calcular faixa etária padronizada
CREATE OR REPLACE FUNCTION dq.faixa_etaria(nascimento DATE) RETURNS TEXT AS $$
DECLARE idade INT;
BEGIN
    idade := EXTRACT(YEAR FROM AGE(nascimento));
    RETURN CASE
        WHEN idade BETWEEN 18 AND 24 THEN '18-24'
        WHEN idade BETWEEN 25 AND 34 THEN '25-34'
        WHEN idade BETWEEN 35 AND 44 THEN '35-44'
        WHEN idade BETWEEN 45 AND 54 THEN '45-54'
        WHEN idade BETWEEN 55 AND 64 THEN '55-64'
        WHEN idade >= 65 THEN '65+'
        ELSE 'Menor de idade'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Calcular faixa de score de crédito
CREATE OR REPLACE FUNCTION dq.faixa_score(score INT) RETURNS TEXT AS $$
BEGIN
    RETURN CASE
        WHEN score BETWEEN 0   AND 300  THEN 'Muito Baixo'
        WHEN score BETWEEN 301 AND 500  THEN 'Baixo'
        WHEN score BETWEEN 501 AND 700  THEN 'Regular'
        WHEN score BETWEEN 701 AND 850  THEN 'Bom'
        WHEN score BETWEEN 851 AND 1000 THEN 'Excelente'
        ELSE 'Inválido'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ================================================================
-- Como executar o DQ completo:
--
-- 1. Carregar dados no Bronze:
--    COPY bronze.clientes FROM '/dados/clientes.csv' CSV HEADER;
--    (repetir para todas as tabelas)
--
-- 2. Executar este script:
--    \i sql/02_silver/data_quality_framework.sql
--
-- 3. Ver scorecard:
--    SELECT * FROM dq.scorecard;
--    SELECT * FROM dq.audit_log WHERE severidade = 'ERROR' ORDER BY qtd_registros DESC;
--
-- 4. Corrigir erros antes de promover para Silver.
-- ================================================================
