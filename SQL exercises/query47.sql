WITH all_ships AS (
    SELECT c.country, s.name
    FROM Classes c
    JOIN Ships s ON s.class = c.class
    UNION
    SELECT c.country, o.ship
    FROM Classes c
    JOIN Outcomes o ON o.ship = c.class
),
flagged AS (
    SELECT a.country, a.name,
           CASE WHEN EXISTS (
                    SELECT 1 FROM Outcomes o
                    WHERE o.ship = a.name AND o.result = 'sunk')
                THEN 1 ELSE 0
           END AS is_sunk
    FROM all_ships a
)
SELECT country
FROM flagged
GROUP BY country
HAVING COUNT(*) = SUM(is_sunk);
