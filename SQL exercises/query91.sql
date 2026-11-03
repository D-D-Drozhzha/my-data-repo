SELECT CAST(AVG(s * 1.0) AS NUMERIC(6,2)) AS avg_paint
FROM (
    SELECT q.Q_ID, ISNULL(SUM(CAST(b.B_VOL AS int)), 0) AS s
    FROM utQ q
    LEFT JOIN utB b ON b.B_Q_ID = q.Q_ID
    GROUP BY q.Q_ID
) t
