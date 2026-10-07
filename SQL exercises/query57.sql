WITH sh AS (
    SELECT name, class FROM Ships
    UNION
    SELECT ship, ship FROM Outcomes
    WHERE ship NOT IN (SELECT name FROM Ships)
),
x AS (
    SELECT sh.class,
           sh.name,
           CASE WHEN EXISTS (
                    SELECT 1 FROM Outcomes o
                    WHERE o.ship = sh.name AND o.result = 'sunk')
                THEN 1 ELSE 0
           END AS is_sunk
    FROM sh
    JOIN Classes c ON c.class = sh.class
)
SELECT class, SUM(is_sunk) AS sunk
FROM x
GROUP BY class
HAVING COUNT(*) >= 3
   AND SUM(is_sunk) > 0;
