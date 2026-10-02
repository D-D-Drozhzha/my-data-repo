SELECT DISTINCT o.battle
FROM Ships s
JOIN Outcomes o ON o.ship = s.name
WHERE s.class = 'Kongo';
