SELECT sh.class, sh.name, cl.country
FROM ships sh
INNER JOIN classes cl ON sh.class = cl.class
WHERE cl.numGuns >= 10
