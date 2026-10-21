SELECT c.country, b.name AS battle
FROM (SELECT DISTINCT country FROM Classes) c
CROSS JOIN Battles b
WHERE NOT EXISTS (
    SELECT 1
    FROM Outcomes o
    LEFT JOIN Ships s ON s.name = o.ship
    JOIN Classes cl
      ON cl.class = s.class OR cl.class = o.ship
    WHERE o.battle = b.name
      AND cl.country = c.country
)
