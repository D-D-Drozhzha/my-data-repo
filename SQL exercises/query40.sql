SELECT maker, MAX(type) AS type
FROM Product
GROUP BY maker
HAVING COUNT(DISTINCT type) = 1 AND COUNT(model) > 1;
