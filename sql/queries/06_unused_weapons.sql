-- Întrebare: există arme care n-au făcut niciun kill? (Dacă da, e un semnal de verificat în generator.)
-- Tehnică: LEFT JOIN + IS NULL, pe weapon și kill_table.
SELECT w.weapon_id, w.name, w.category
FROM weapon AS w
LEFT JOIN kill_table AS k ON k.weapon_id = w.weapon_id
WHERE k.kill_id IS NULL
ORDER BY w.name;
