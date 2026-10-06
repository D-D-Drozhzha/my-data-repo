SELECT s.name
FROM Ships s
JOIN Classes c ON c.class = s.class
WHERE c.country = 'Japan'
  AND c.type = 'bb'
  AND (c.numGuns >= 9 OR c.numGuns IS NULL)
  AND (c.bore < 19 OR c.bore IS NULL)
  AND (c.displacement <= 65000 OR c.displacement IS NULL)
