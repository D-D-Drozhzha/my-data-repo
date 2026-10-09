WITH r AS (
    SELECT town_from, town_to, COUNT(*) AS cnt
    FROM Trip
    GROUP BY town_from, town_to
)
SELECT COUNT(*) AS qty
FROM r
WHERE cnt = (SELECT MAX(cnt) FROM r)
