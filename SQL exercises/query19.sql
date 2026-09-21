SELECT pro.maker, AVG(l.screen)
FROM Product pro
INNER JOIN Laptop l ON pro.model = l.model
GROUP BY maker
