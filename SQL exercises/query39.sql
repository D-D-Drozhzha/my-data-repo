SELECT DISTINCT o1.ship
FROM Outcomes o1
JOIN Battles b1 ON o1.battle = b1.name
JOIN Outcomes o2 ON o2.ship = o1.ship
JOIN Battles b2 ON o2.battle = b2.name
WHERE o1.result = 'damaged'
  AND b2.date > b1.date;
