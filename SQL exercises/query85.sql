SELECT maker
FROM Product
GROUP BY maker
HAVING COUNT(DISTINCT type) = 1
   AND (    MAX(type) = 'Printer'
         OR (MAX(type) = 'PC' AND COUNT(model) >= 3) )
