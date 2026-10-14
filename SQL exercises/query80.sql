SELECT DISTINCT maker
FROM Product
EXCEPT
SELECT maker
FROM Product
WHERE type = 'PC'
  AND model NOT IN (SELECT model FROM PC)
