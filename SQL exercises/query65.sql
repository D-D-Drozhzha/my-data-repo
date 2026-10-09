WITH t AS (
    SELECT DISTINCT maker, type,
           CASE type
               WHEN 'PC'     THEN 1
               WHEN 'Laptop' THEN 2
               ELSE 3
           END AS ord
    FROM Product
)
SELECT ROW_NUMBER() OVER (ORDER BY maker, ord) AS num,
       CASE WHEN ROW_NUMBER() OVER (PARTITION BY maker ORDER BY ord) = 1
            THEN maker ELSE ''
       END AS maker,
       type
FROM t
ORDER BY num
