SELECT c.class, COUNT(DISTINCT t.ship) AS sunk
FROM Classes c
LEFT JOIN (
    SELECT o.ship, COALESCE(s.class, o.ship) AS class
    FROM Outcomes o
    LEFT JOIN Ships s ON s.name = o.ship
    WHERE o.result = 'sunk'
) t ON t.class = c.class
GROUP BY c.class
