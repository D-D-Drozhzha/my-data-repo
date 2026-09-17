SELECT AVG(pc.speed) AS avg_speed
FROM PC pc
INNER JOIN Product pr ON pc.model = pr.model
WHERE pr.maker = 'A'
