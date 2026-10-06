SELECT c.class,
       COALESCE(
           (SELECT s.launched
            FROM Ships s
            WHERE s.name = c.class AND s.class = c.class),
           (SELECT MIN(s.launched)
            FROM Ships s
            WHERE s.class = c.class)
       ) AS year
FROM Classes c
