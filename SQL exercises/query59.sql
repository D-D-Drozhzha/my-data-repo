SELECT point, SUM(amount) AS balance
FROM (
    SELECT point, inc AS amount FROM Income_o
    UNION ALL
    SELECT point, -out FROM Outcome_o
) t
GROUP BY point
