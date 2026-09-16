SELECT DISTINCT pr.maker, l.speed
FROM Product pr
INNER JOIN Laptop l ON pr.model = l.model
WHERE hd >= 10
