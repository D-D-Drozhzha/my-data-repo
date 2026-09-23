SELECT maker, hd
FROM
(SELECT pro.maker, AVG(hd) AS hd
 FROM Product pro
 INNER JOIN PC pc ON pro.model = pc.model
 GROUP BY maker) cte1
WHERE maker IN (SELECT maker FROM Product WHERE type = 'Printer')
