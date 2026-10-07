SELECT m.maker, t.type,
       CAST(100.0 *
            (SELECT COUNT(*) FROM Product p
             WHERE p.maker = m.maker AND p.type = t.type)
          / (SELECT COUNT(*) FROM Product p
             WHERE p.maker = m.maker)
       AS NUMERIC(5,2)) AS prc
FROM (SELECT DISTINCT maker FROM Product) m
CROSS JOIN (SELECT DISTINCT type FROM Product) t;
