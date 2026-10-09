SELECT name
FROM Passenger
WHERE ID_psg IN (
    SELECT ID_psg
    FROM Pass_in_trip
    GROUP BY ID_psg, place
    HAVING COUNT(*) > 1
);
