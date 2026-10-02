SELECT s.class
FROM Ships s
JOIN Outcomes o ON o.ship = s.name
WHERE o.result = 'sunk'

UNION

SELECT c.class
FROM Classes c
JOIN Outcomes o ON o.ship = c.class
WHERE o.result = 'sunk'
