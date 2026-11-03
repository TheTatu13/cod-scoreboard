-- Întrebare: câți jucători înregistrați nu au jucat niciun meci?
-- Tehnică: tiparul „cine NU are...": LEFT JOIN + WHERE coloană_din_dreapta IS NULL.
SELECT
    COUNT(*)                                  AS registered_players,
    SUM(mp.player_id IS NULL)                 AS never_played,
    ROUND(100 * SUM(mp.player_id IS NULL) / COUNT(*), 1) AS never_played_pct
FROM player AS p
LEFT JOIN (SELECT DISTINCT player_id FROM match_player) AS mp ON mp.player_id = p.player_id;
