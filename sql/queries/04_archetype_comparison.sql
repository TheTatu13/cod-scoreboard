-- Întrebare: cât de mult influențează arhetipul performanța? Se vede diferența de K/D?
-- Tehnică: view peste view (v_archetype_stats se bazează pe v_player_stats).
SELECT archetype, players, matches_played, total_kills, total_deaths, kd_ratio
FROM v_archetype_stats
ORDER BY kd_ratio DESC;
