SELECT TOP 1 WITH TIES p.name,
       SUM((DATEDIFF(mi, t.time_out, t.time_in) + 1440) % 1440) AS minutes
FROM Pass_in_trip pt
JOIN Trip t      ON t.trip_no = pt.trip_no
JOIN Passenger p ON p.ID_psg  = pt.ID_psg
GROUP BY pt.ID_psg, p.name
ORDER BY minutes DESC
