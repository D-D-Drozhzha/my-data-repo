SELECT DISTINCT pc.model, pc.price
FROM PC pc
INNER JOIN Product pr ON pc.model = pr.model
WHERE pr.maker LIKE 'B%'

UNION

SELECT DISTINCT l.model, l.price
FROM Laptop l
INNER JOIN Product pr ON l.model = pr.model
WHERE pr.maker LIKE 'B%'

UNION

SELECT DISTINCT p.model, p.price
FROM Printer p
INNER JOIN Product pr ON p.model = pr.model
WHERE pr.maker LIKE 'B%'
