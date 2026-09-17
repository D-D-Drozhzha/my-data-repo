SELECT model, price
FROM Printer
WHERE price = (SELECT MAX(price) AS price
               FROM Printer)
