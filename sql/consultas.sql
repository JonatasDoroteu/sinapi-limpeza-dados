-- Consultas sobre os preços da Bahia, regime sem_desoneracao.

-- 1. Preço médio por classificação em setembro de 2026.
SELECT
    d.classificacao,
    ROUND(AVG(f.preco), 2) AS preco_medio,
    COUNT(*) AS quantidade
FROM fato_preco AS f
LEFT JOIN dim_insumo AS d USING (codigo)
WHERE f.uf = 'BA'
  AND f.referencia = '2026-09'
  AND f.regime = 'sem_desoneracao'
GROUP BY d.classificacao
ORDER BY d.classificacao;

-- 2. Variação percentual por insumo entre junho e setembro, somente com preço nos dois meses.
-- O resultado contém as dez maiores altas e as dez maiores quedas.
WITH variacoes AS (
    SELECT
        jun.codigo,
        d.descricao,
        d.unidade,
        d.classificacao,
        jun.preco AS preco_junho,
        set.preco AS preco_setembro,
        100 * (set.preco - jun.preco) / jun.preco AS variacao_pct
    FROM fato_preco AS jun
    JOIN fato_preco AS set USING (codigo, uf, regime)
    LEFT JOIN dim_insumo AS d USING (codigo)
    WHERE jun.uf = 'BA'
      AND jun.referencia = '2026-06'
      AND jun.regime = 'sem_desoneracao'
      AND set.referencia = '2026-09'
),
altas AS (
    SELECT
        'alta' AS tipo,
        *,
        ROW_NUMBER() OVER (ORDER BY variacao_pct DESC, codigo) AS posicao
    FROM variacoes
),
quedas AS (
    SELECT
        'queda' AS tipo,
        *,
        ROW_NUMBER() OVER (ORDER BY variacao_pct ASC, codigo) AS posicao
    FROM variacoes
)
SELECT tipo, codigo, descricao, unidade, classificacao,
       preco_junho, preco_setembro, ROUND(variacao_pct, 2) AS variacao_pct
FROM altas
WHERE posicao <= 10
UNION ALL
SELECT tipo, codigo, descricao, unidade, classificacao,
       preco_junho, preco_setembro, ROUND(variacao_pct, 2) AS variacao_pct
FROM quedas
WHERE posicao <= 10
ORDER BY tipo, variacao_pct DESC;

-- 3. Insumos que perderam ou ganharam preço válido entre junho e setembro.
-- A ausência considera a tabela de preços válidos, não afirma que o código sumiu da planilha.
WITH situacao AS (
    SELECT
        CASE
            WHEN jun.codigo IS NOT NULL AND set.codigo IS NULL THEN 'perdeu preço'
            WHEN jun.codigo IS NULL AND set.codigo IS NOT NULL THEN 'ganhou preço'
        END AS tipo,
        COALESCE(jun.codigo, set.codigo) AS codigo,
        d.descricao,
        d.unidade
    FROM (
        SELECT codigo
        FROM fato_preco
        WHERE uf = 'BA' AND referencia = '2026-06' AND regime = 'sem_desoneracao'
    ) AS jun
    FULL OUTER JOIN (
        SELECT codigo
        FROM fato_preco
        WHERE uf = 'BA' AND referencia = '2026-09' AND regime = 'sem_desoneracao'
    ) AS set USING (codigo)
    LEFT JOIN dim_insumo AS d ON d.codigo = COALESCE(jun.codigo, set.codigo)
    WHERE jun.codigo IS NULL OR set.codigo IS NULL
),
tipos AS (
    SELECT *
    FROM (VALUES ('perdeu preço'), ('ganhou preço')) AS t(tipo)
),
contagens AS (
    SELECT t.tipo, COUNT(s.codigo) AS total
    FROM tipos AS t
    LEFT JOIN situacao AS s USING (tipo)
    GROUP BY t.tipo
),
exemplos AS (
    SELECT
        tipo,
        codigo,
        descricao,
        unidade,
        ROW_NUMBER() OVER (PARTITION BY tipo ORDER BY codigo) AS posicao
    FROM situacao
)
SELECT tipo, total, NULL::VARCHAR AS codigo, NULL::VARCHAR AS descricao, NULL::VARCHAR AS unidade
FROM contagens
UNION ALL
SELECT e.tipo, c.total, e.codigo, e.descricao, e.unidade
FROM exemplos AS e
JOIN contagens AS c USING (tipo)
WHERE e.posicao <= 10
ORDER BY tipo, codigo NULLS FIRST;

-- 4. Ranking das variações por classificação, usando RANK para conservar empates.
WITH variacoes AS (
    SELECT
        jun.codigo,
        d.descricao,
        d.unidade,
        d.classificacao,
        jun.preco AS preco_junho,
        set.preco AS preco_setembro,
        100 * (set.preco - jun.preco) / jun.preco AS variacao_pct
    FROM fato_preco AS jun
    JOIN fato_preco AS set USING (codigo, uf, regime)
    JOIN dim_insumo AS d USING (codigo)
    WHERE jun.uf = 'BA'
      AND jun.referencia = '2026-06'
      AND jun.regime = 'sem_desoneracao'
      AND set.referencia = '2026-09'
),
ranqueadas AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY classificacao
            ORDER BY variacao_pct DESC
        ) AS posicao_na_classificacao
    FROM variacoes
)
SELECT classificacao, posicao_na_classificacao, codigo, descricao, unidade,
       preco_junho, preco_setembro, ROUND(variacao_pct, 2) AS variacao_pct
FROM ranqueadas
WHERE posicao_na_classificacao <= 3
ORDER BY variacao_pct DESC, classificacao, posicao_na_classificacao, codigo;
