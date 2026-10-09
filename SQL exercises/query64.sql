WITH i AS (
    SELECT point, date, SUM(inc) AS s
    FROM Income
    GROUP BY point, date
),
o AS (
    SELECT point, date, SUM(out) AS s
    FROM Outcome
    GROUP BY point, date
)
SELECT COALESCE(i.point, o.point) AS point,
       COALESCE(i.date, o.date)   AS date,
       CASE WHEN i.point IS NULL THEN 'out' ELSE 'inc' END AS operation,
       COALESCE(i.s, o.s)         AS money_sum
FROM i
FULL JOIN o ON o.point = i.point AND o.date = i.date
WHERE i.point IS NULL OR o.point IS NULL
