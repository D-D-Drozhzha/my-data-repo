SELECT c.name,
       SUM((DATEDIFF(mi, t.time_out, t.time_in) + 1440) % 1440) AS minutes
FROM (SELECT DISTINCT trip_no, date FROM Pass_in_trip) f
JOIN Trip t    ON t.trip_no = f.trip_no
JOIN Company c ON c.ID_comp = t.id_comp
GROUP BY c.ID_comp, c.name
