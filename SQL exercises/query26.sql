SELECT AVG(price)
FROM
(SELECT maker, code, price, ram, hd
 FROM Product pro
 INNER JOIN PC pc ON pro.model = pc.model
 WHERE maker = 'A'

 UNION

 SELECT maker, code, price, ram, hd
 FROM Product pro
 INNER JOIN Laptop l ON pro.model = l.model
 WHERE maker = 'A') cte
