SELECT name
FROM Ships
WHERE name = class

UNION

SELECT o.ship
FROM Outcomes o
JOIN Classes c ON o.ship = c.class;
