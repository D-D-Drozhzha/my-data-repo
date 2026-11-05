SELECT p.maker,
       MAX(CASE WHEN p.type = 'Laptop'  THEN u.price END) AS max_laptop,
       MAX(CASE WHEN p.type = 'PC'      THEN u.price END) AS max_pc,
       MAX(CASE WHEN p.type = 'Printer' THEN u.price END) AS max_printer
FROM Product p
JOIN (
    SELECT model, price FROM Laptop
    UNION ALL
    SELECT model, price FROM PC
    UNION ALL
    SELECT model, price FROM Printer
) u ON u.model = p.model
GROUP BY p.maker
HAVING COUNT(u.price) > 0
