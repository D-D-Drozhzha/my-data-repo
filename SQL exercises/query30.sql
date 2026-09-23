SELECT point, date, SUM(outcome), SUM(income)
FROM
(SELECT point, date, NULL AS outcome, SUM(inc) AS income
 FROM Income
 GROUP BY point, date

 UNION

 SELECT point, date, SUM(out) AS outcome, NULL AS income
 FROM Outcome o
 GROUP BY point, date) cte1
GROUP BY point, date
ORDER BY point
