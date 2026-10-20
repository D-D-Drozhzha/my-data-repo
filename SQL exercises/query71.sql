SELECT maker FROM Product WHERE type = 'PC'
EXCEPT
SELECT maker FROM Product
WHERE type = 'PC'
  AND model NOT IN (SELECT model FROM PC);
