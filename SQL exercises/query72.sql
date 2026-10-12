SELECT TOP 1 WITH TIES p.name, COUNT(*) AS qty
FROM Pass_in_trip pt
JOIN Trip t      ON t.trip_no = pt.trip_no
JOIN Passenger p ON p.ID_psg  = pt.ID_psg
GROUP BY pt.ID_psg, p.name
HAVING COUNT(DISTINCT t.id_comp) = 1
ORDER BY qty DESC;
