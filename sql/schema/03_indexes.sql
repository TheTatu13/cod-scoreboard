-- Indexuri adăugate în Faza 2, justificate cu EXPLAIN ANALYZE (vezi docs/optimization/faza-2-indexuri.md).
-- Sunt indexuri „acoperitoare": conțin ambele coloane folosite de interogare, deci MySQL
-- nu mai citește rândurile din tabel, doar indexul.
-- Rulează automat în Docker, după 02_views.sql. Pe o bază existentă: rulează-l o singură dată.

-- v_weapon_stats: GROUP BY weapon_id + SUM(is_headshot)
ALTER TABLE kill_table ADD INDEX idx_kill_weapon_headshot (weapon_id, is_headshot);

-- 09_top_headshot_players.sql: GROUP BY killer_id + SUM(is_headshot)
ALTER TABLE kill_table ADD INDEX idx_kill_killer_headshot (killer_id, is_headshot);
