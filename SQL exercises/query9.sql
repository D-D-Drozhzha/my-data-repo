SELECT DISTINCT pr.maker
FROM Product pr
INNER JOIN PC pc ON pr.model = pc.model
WHERE speed >= 450
