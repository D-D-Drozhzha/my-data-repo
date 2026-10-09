WITH days AS (
    SELECT CAST('2003-04-01' AS datetime) AS d
    UNION ALL
    SELECT DATEADD(dd, 1, d) FROM days WHERE d < '2003-04-07'
),
r AS (
    SELECT DISTINCT p.date, p.trip_no
    FROM Pass_in_trip p
    JOIN Trip t ON t.trip_no = p.trip_no
    WHERE t.town_from = 'Rostov'
)
SELECT days.d AS date, COUNT(r.trip_no) AS qty
FROM days
LEFT JOIN r ON r.date = days.d
GROUP BY days.d;
