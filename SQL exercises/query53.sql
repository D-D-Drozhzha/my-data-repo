SELECT CAST(AVG(numGuns * 1.0) AS NUMERIC(6,2)) AS avg_numGuns
FROM Classes
WHERE type = 'bb';
