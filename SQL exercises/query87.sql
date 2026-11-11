SELECT p.name, COUNT(*) AS qty
FROM Pass_in_trip pt
JOIN Trip t      ON t.trip_no = pt.trip_no
JOIN Passenger p ON p.ID_psg  = pt.ID_psg
WHERE t.town_to = 'Moscow'
  AND (SELECT TOP 1 t2.town_from
       FROM Pass_in_trip pt2
       JOIN Trip t2 ON t2.trip_no = pt2.trip_no
       WHERE pt2.ID_psg = pt.ID_psg
       ORDER BY pt2.date, t2.time_out) <> 'Moscow'
GROUP BY pt.ID_psg, p.name
HAVING COUNT(*) > 1;
