SELECT model, type
FROM Product
WHERE UPPER(model) NOT LIKE '%[^A-Z]%' OR model NOT LIKE '%[^0-9]%'
