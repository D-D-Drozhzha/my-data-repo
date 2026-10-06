WITH sh AS (
    SELECT name, class FROM Ships
    UNION
    SELECT ship, ship FROM Outcomes
),
all_ships AS (
    SELECT sh.name, c.displacement, c.numGuns
    FROM sh
    JOIN Classes c ON c.class = sh.class
)
SELECT a.name
FROM all_ships a
WHERE a.numGuns >= ALL (
    SELECT b.numGuns
    FROM all_ships b
    WHERE b.displacement = a.displacement
)
