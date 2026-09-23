SELECT COUNT(maker) AS num_maker
FROM Product
WHERE maker IN
(SELECT maker
 FROM Product
 GROUP BY maker
 HAVING COUNT(model) = 1)
