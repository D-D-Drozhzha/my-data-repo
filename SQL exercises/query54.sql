WITH sh AS (
    SELECT name, class FROM Ships
    UNION
    SELECT ship, ship FROM Outcomes
)
SELECT CAST(AVG(c.numGuns * 1.0) AS NUMERIC(6,2)) AS avg_numGuns
FROM sh
JOIN Classes c ON c.class = sh.class
WHERE c.type = 'bb'
