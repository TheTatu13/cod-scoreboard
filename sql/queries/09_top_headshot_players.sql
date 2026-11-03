-- Întrebare: cine are cel mai mare procent de headshot (minim 100 de kill-uri)?
-- Tehnică: agregare directă pe kill_table, JOIN cu player pentru nume.
SELECT
    p.gamertag,
    p.archetype,
    COUNT(*)                                  AS kills,
    SUM(k.is_headshot)                        AS headshots,
    ROUND(100 * SUM(k.is_headshot) / COUNT(*), 1) AS headshot_pct
FROM kill_table AS k
JOIN player AS p ON p.player_id = k.killer_id
GROUP BY p.player_id, p.gamertag, p.archetype
HAVING COUNT(*) >= 100
ORDER BY headshot_pct DESC
LIMIT 10;
