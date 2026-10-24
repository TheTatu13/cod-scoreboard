SELECT p.gamertag, COUNT(*) AS meciuri
FROM match_player mp
JOIN player p ON mp.player_id = p.player_id
GROUP BY mp.player_id, p.gamertag
HAVING COUNT(*) >= 15;