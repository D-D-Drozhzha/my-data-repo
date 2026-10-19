SELECT DISTINCT o.battle
FROM Outcomes o
LEFT JOIN Ships s ON s.name = o.ship
JOIN Classes c
  ON c.class = CASE WHEN s.class IS NOT NULL
                    THEN s.class
                    ELSE o.ship
               END
GROUP BY o.battle, c.country
HAVING COUNT(DISTINCT o.ship) >= 3
