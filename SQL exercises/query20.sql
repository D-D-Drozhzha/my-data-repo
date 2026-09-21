SELECT maker, COUNT(model) AS num_model
FROM Product
WHERE type = 'PC'
GROUP BY maker
HAVING COUNT(model) >= 3
