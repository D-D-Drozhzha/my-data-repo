SELECT s.name
FROM Ships s
JOIN Classes c ON c.class = s.class
WHERE c.bore = 16

UNION

SELECT o.ship
FROM Outcomes o
JOIN Classes c ON c.class = o.ship
WHERE c.bore = 16;
