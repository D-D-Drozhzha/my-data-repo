SELECT name,
       CONVERT(char(10), DATEADD(dd, 1, EOMONTH(date, -1)), 120) AS first_day,
       CONVERT(char(10), EOMONTH(date), 120) AS last_day
FROM Battles
