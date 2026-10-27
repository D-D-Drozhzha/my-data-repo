SELECT code, avg_price
FROM (
    SELECT code,
           AVG(price) OVER (ORDER BY code
                            ROWS BETWEEN CURRENT ROW AND 5 FOLLOWING) AS avg_price,
           COUNT(*)   OVER (ORDER BY code
                            ROWS BETWEEN CURRENT ROW AND 5 FOLLOWING) AS cnt
    FROM PC
) t
WHERE cnt = 6
