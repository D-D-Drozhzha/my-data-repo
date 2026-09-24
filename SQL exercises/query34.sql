SELECT name
FROM Ships s
INNER JOIN Classes c ON s.class = c.class
WHERE launched >= 1922 AND displacement > 35000 AND type = 'bb'
