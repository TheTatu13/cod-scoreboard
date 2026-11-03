-- Întrebare: cum se compară categoriile de arme (AR, SMG, Sniper...) la kill-uri și headshot?
-- Tehnică: GROUP BY pe o coloană dintr-un view; procentul se calculează din sume, nu din medii de procente.
SELECT
    category,
    COUNT(*)                         AS weapons,
    SUM(total_kills)                 AS kills,
    SUM(headshots)                   AS headshots,
    ROUND(100 * SUM(headshots) / NULLIF(SUM(total_kills), 0), 1) AS headshot_pct
FROM v_weapon_stats
GROUP BY category
ORDER BY kills DESC;
