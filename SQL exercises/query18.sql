SELECT DISTINCT pro.maker, pri.price
FROM Product pro
INNER JOIN Printer pri ON pro.model = pri.model
WHERE price = (SELECT MIN(price) FROM Printer WHERE color = 'y') AND color = 'y'
