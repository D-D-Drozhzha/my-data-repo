SELECT o.ship
FROM Outcomes o
INNER JOIN Battles b ON o.battle = b.name
WHERE result = 'sunk' AND b.name = 'North Atlantic'
