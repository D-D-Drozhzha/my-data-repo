SELECT maker, model, type
FROM (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY model ASC)  AS rn_asc,
           ROW_NUMBER() OVER (ORDER BY model DESC) AS rn_desc
    FROM Product
) t
WHERE rn_asc > 3
  AND rn_desc > 3
