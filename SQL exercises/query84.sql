SELECT c.name,
       SUM(CASE WHEN DAY(pt.date) BETWEEN 1  AND 10 THEN 1 ELSE 0 END) AS days_1_10,
       SUM(CASE WHEN DAY(pt.date) BETWEEN 11 AND 20 THEN 1 ELSE 0 END) AS days_11_20,
       SUM(CASE WHEN DAY(pt.date) > 20             THEN 1 ELSE 0 END) AS days_21_30
FROM Pass_in_trip pt
JOIN Trip t    ON t.trip_no = pt.trip_no
JOIN Company c ON c.ID_comp = t.id_comp
WHERE pt.date >= '20030401' AND pt.date < '20030501'
GROUP BY c.ID_comp, c.name;
