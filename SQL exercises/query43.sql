SELECT name
FROM Battles
WHERE YEAR(date) NOT IN (
    SELECT launched
    FROM Ships
    WHERE launched IS NOT NULL
);
