-- Întrebare: ce hărți au cele mai multe kill-uri pe meci? (top 10, doar hărți cu minim 5 meciuri)
-- Tehnică: view-ul v_map_stats face deja JOIN-urile; aici doar filtrăm și ordonăm.
SELECT map_name, game_name, design_style, matches_played, total_kills, kills_per_match
FROM v_map_stats
WHERE matches_played >= 5
ORDER BY kills_per_match DESC
LIMIT 10;
