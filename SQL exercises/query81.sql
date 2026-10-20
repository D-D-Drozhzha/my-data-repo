WITH m AS (
    SELECT YEAR(date) AS y, MONTH(date) AS mo, SUM(out) AS s
    FROM Outcome
    GROUP BY YEAR(date), MONTH(date)
)
SELECT o.*
FROM Outcome o
JOIN m ON YEAR(o.date) = m.y AND MONTH(o.date) = m.mo
WHERE m.s = (SELECT MAX(s) FROM m);
