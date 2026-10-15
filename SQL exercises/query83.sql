SELECT s.name
FROM Ships s
JOIN Classes c ON c.class = s.class
WHERE CASE WHEN c.numGuns = 8          THEN 1 ELSE 0 END
    + CASE WHEN c.bore = 15            THEN 1 ELSE 0 END
    + CASE WHEN c.displacement = 32000 THEN 1 ELSE 0 END
    + CASE WHEN c.type = 'bb'          THEN 1 ELSE 0 END
    + CASE WHEN s.launched = 1915      THEN 1 ELSE 0 END
    + CASE WHEN s.class = 'Kongo'      THEN 1 ELSE 0 END
    + CASE WHEN c.country = 'USA'      THEN 1 ELSE 0 END
    >= 4
