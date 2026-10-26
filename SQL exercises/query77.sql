WITH d AS (
    SELECT pt.date, COUNT(DISTINCT pt.trip_no) AS qty
    FROM Pass_in_trip pt
    JOIN Trip t ON t.trip_no = pt.trip_no
    WHERE t.town_from = 'Rostov'
    GROUP BY pt.date
)
SELECT qty, date
FROM d
WHERE qty = (SELECT MAX(qty) FROM d)
