SELECT point, SUM(amount) AS balance
FROM (
    SELECT point, inc AS amount
    FROM Income_o
    WHERE date < '20010415'
    UNION ALL
    SELECT point, -out
    FROM Outcome_o
    WHERE date < '20010415'
) AS t
GROUP BY point
