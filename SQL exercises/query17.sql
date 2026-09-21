SELECT DISTINCT p.type, l.model, l.speed
FROM Product p
INNER JOIN Laptop l ON p.model = l.model
WHERE l.speed < (SELECT MIN(speed) FROM PC)
