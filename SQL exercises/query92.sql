WITH sq AS (
    SELECT b.B_Q_ID
    FROM utB b
    JOIN utV v ON v.V_ID = b.B_V_ID
    GROUP BY b.B_Q_ID
    HAVING SUM(CASE WHEN v.V_COLOR = 'R' THEN CAST(b.B_VOL AS int) ELSE 0 END) = 255
       AND SUM(CASE WHEN v.V_COLOR = 'G' THEN CAST(b.B_VOL AS int) ELSE 0 END) = 255
       AND SUM(CASE WHEN v.V_COLOR = 'B' THEN CAST(b.B_VOL AS int) ELSE 0 END) = 255
),
not_empty AS (
    SELECT B_V_ID
    FROM utB
    GROUP BY B_V_ID
    HAVING SUM(CAST(B_VOL AS int)) < 255
)
SELECT q.Q_NAME
FROM utQ q
JOIN sq ON sq.B_Q_ID = q.Q_ID
WHERE NOT EXISTS (
    SELECT 1
    FROM utB b
    JOIN not_empty ne ON ne.B_V_ID = b.B_V_ID
    WHERE b.B_Q_ID = q.Q_ID
);
