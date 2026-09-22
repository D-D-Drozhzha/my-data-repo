SELECT pro.maker, MAX(pc.price)
FROM Product pro
INNER JOIN PC pc ON pro.model = pc.model
GROUP BY maker
