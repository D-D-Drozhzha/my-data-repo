SELECT COUNT(*) AS qty
FROM (
    SELECT TOP 1 WITH TIES COUNT(*) AS cnt
    FROM Trip
    GROUP BY CASE WHEN town_from < town_to THEN town_from ELSE town_to END,
             CASE WHEN town_from < town_to THEN town_to ELSE town_from END
    ORDER BY cnt DESC
) t;
