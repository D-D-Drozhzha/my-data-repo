WITH m AS (
    SELECT maker, COUNT(*) AS qty
    FROM Product
    GROUP BY maker
)
SELECT maker, qty
FROM m
WHERE qty = (SELECT MAX(qty) FROM m)
   OR qty = (SELECT MIN(qty) FROM m)
