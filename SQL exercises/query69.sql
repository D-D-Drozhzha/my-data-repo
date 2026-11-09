WITH d AS (
    SELECT point, date, SUM(amount) AS day_sum
    FROM (
        SELECT point, date, inc AS amount FROM Income
        UNION ALL
        SELECT point, date, -out FROM Outcome
    ) t
    GROUP BY point, date
)
SELECT point,
       CONVERT(char(10), date, 103) AS day,
       SUM(day_sum) OVER (PARTITION BY point ORDER BY date
                          ROWS UNBOUNDED PRECEDING) AS rem
FROM d;
