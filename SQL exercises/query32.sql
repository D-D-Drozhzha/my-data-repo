SELECT country,
       CAST(AVG(POWER(bore, 3) / 2) AS NUMERIC(6, 2)) AS weight
FROM (
    SELECT c.country, c.bore, s.name
    FROM Classes c
    JOIN Ships s ON s.class = c.class

    UNION

    SELECT c.country, c.bore, o.ship
    FROM Classes c
    JOIN Outcomes o ON o.ship = c.class
) AS all_ships
GROUP BY country
