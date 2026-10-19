SELECT country, class
FROM Classes
WHERE country = 'Russia'
   OR NOT EXISTS (
       SELECT 1 FROM Classes WHERE country = 'Russia'
   )
