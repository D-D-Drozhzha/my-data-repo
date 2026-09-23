SELECT i.point, i.date, i.inc, o.out
FROM Income_o i
LEFT JOIN Outcome_o o ON i.point = o.point AND i.date = o.date

UNION

SELECT o.point, o.date, i.inc, o.out
FROM Income_o i
RIGHT JOIN Outcome_o o ON i.point = o.point AND i.date = o.date
