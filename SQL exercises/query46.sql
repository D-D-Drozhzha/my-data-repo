SELECT o.ship, c.displacement, c.numGuns
FROM Outcomes o
LEFT JOIN Ships s ON s.name = o.ship
LEFT JOIN Classes c ON c.class = s.class
                    OR (s.name IS NULL AND c.class = o.ship)
WHERE o.battle = 'Guadalcanal'
