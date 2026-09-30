SELECT p.maker,
       CASE WHEN COUNT(*) = COUNT(u.price)
            THEN MAX(u.price)
       END AS max_price
FROM Product p
JOIN (
    SELECT model, price FROM PC
    UNION ALL
    SELECT model, price FROM Laptop
    UNION ALL
    SELECT model, price FROM Printer
) u ON p.model = u.model
GROUP BY p.maker;
