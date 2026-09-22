SELECT pro.maker
FROM Product pro
INNER JOIN PC pc ON pro.model = pc.model
WHERE pc.speed >= 750

INTERSECT

SELECT pro.maker
FROM Product pro
INNER JOIN Laptop l ON pro.model = l.model
WHERE l.speed >= 750
