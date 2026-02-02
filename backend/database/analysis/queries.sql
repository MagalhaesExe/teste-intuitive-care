-- Query 1
WITH periodos_extremos AS (
    -- Identifica o primeiro e o último trimestre disponível para CADA operadora
    SELECT 
        registro_ans,
        razao_social,
        MIN(ano * 10 + trimestre) as primeiro_periodo,
        MAX(ano * 10 + trimestre) as ultimo_periodo
    FROM despesas_consolidadas
    GROUP BY registro_ans, razao_social
),
valores_periodos AS (
    -- Busca os valores especificamente nesses trimestres identificados
    SELECT 
        pe.registro_ans,
        pe.razao_social,
        d_ini.valor_despesa as valor_inicial,
        d_fim.valor_despesa as valor_final
    FROM periodos_extremos pe
    JOIN despesas_consolidadas d_ini ON pe.registro_ans = d_ini.registro_ans 
         AND (d_ini.ano * 10 + d_ini.trimestre) = pe.primeiro_periodo
    JOIN despesas_consolidadas d_fim ON pe.registro_ans = d_fim.registro_ans 
         AND (d_fim.ano * 10 + d_fim.trimestre) = pe.ultimo_periodo
    WHERE d_ini.valor_despesa > 0
)
-- Calcula a variação percentual
SELECT 
    razao_social,
    registro_ans,
    valor_inicial,
    valor_final,
    ROUND(((valor_final - valor_inicial) / valor_inicial) * 100, 2) as crescimento_percentual
FROM valores_periodos
WHERE valor_inicial <> valor_final
ORDER BY crescimento_percentual DESC
LIMIT 5;

-- Query 2
-- Mostra o Total acumulado e a média por operadora em cada estado
SELECT 
    uf,
    SUM(valor_despesa) as despesa_total_estado,
    COUNT(DISTINCT registro_ans) as qtd_operadoras,
    ROUND(SUM(valor_despesa) / COUNT(DISTINCT registro_ans), 2) as media_por_operadora
FROM despesas_consolidadas
WHERE uf <> 'NI' -- Remove registros com UF não identificada
GROUP BY uf
ORDER BY despesa_total_estado DESC
LIMIT 5;

-- Query 3
WITH media_global AS (
    -- Calcula a média de despesa de todos os lançamentos no banco
    SELECT AVG(valor_despesa) as media_geral 
    FROM despesas_consolidadas
),
contagem_acima_media AS (
    -- Conta quantos trimestres cada operadora ficou acima da média global
    SELECT 
        registro_ans,
        razao_social,
        COUNT(*) as frequencia_acima_media
    FROM despesas_consolidadas, media_global
    WHERE valor_despesa > media_global.media_geral
    GROUP BY registro_ans, razao_social
)
-- Filtra apenas quem atingiu a meta de 2 ou mais trimestres
SELECT 
    razao_social,
    frequencia_acima_media
FROM contagem_acima_media
WHERE frequencia_acima_media >= 2
ORDER BY frequencia_acima_media DESC;