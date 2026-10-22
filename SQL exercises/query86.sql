SELECT maker,
       STRING_AGG(type, '/') WITHIN GROUP (ORDER BY type) AS types
FROM (SELECT DISTINCT maker, type FROM Product) t
GROUP BY maker;
