SELECT DISTINCT pc1.model, pc2.model, pc1.speed, pc1.ram
FROM PC pc1, PC pc2
WHERE pc1.speed = pc2.speed AND pc1.ram = pc2.ram AND pc1.model > pc2.model
