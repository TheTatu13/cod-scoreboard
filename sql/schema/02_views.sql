-- Views analitice (Faza 2). Rulează automat în Docker, după 01_schema.sql (ordine alfabetică).
-- Sunt idempotente: `CREATE OR REPLACE VIEW` poate fi rulat de câte ori vrei.
-- Idee: o view e un SELECT salvat sub un nume. Nu stochează date, le recalculează la fiecare citire.

-- Statistici per jucător, doar pentru cei care au jucat cel puțin un meci.
-- K/D = kills / deaths. NULLIF(deaths, 0) dă NULL în loc de eroare când deaths = 0.
CREATE OR REPLACE VIEW v_player_stats AS
SELECT
    p.player_id,
    p.gamertag,
    p.platform,
    p.archetype,
    COUNT(*)                                   AS matches_played,
    SUM(mp.kills)                              AS total_kills,
    SUM(mp.deaths)                             AS total_deaths,
    SUM(mp.assists)                            AS total_assists,
    ROUND(SUM(mp.kills) / NULLIF(SUM(mp.deaths), 0), 2) AS kd_ratio,
    ROUND(AVG(mp.score), 1)                    AS avg_score
FROM player AS p
JOIN match_player AS mp ON mp.player_id = p.player_id
GROUP BY p.player_id, p.gamertag, p.platform, p.archetype;

-- Statistici per hartă: câte meciuri s-au jucat și câte kill-uri au căzut în medie pe meci.
-- LEFT JOIN: o hartă fără niciun meci apare totuși, cu 0.
CREATE OR REPLACE VIEW v_map_stats AS
SELECT
    mp.map_id,
    mp.name        AS map_name,
    g.name         AS game_name,
    mp.size_category,
    mp.design_style,
    COUNT(DISTINCT m.match_id)                                   AS matches_played,
    COUNT(k.kill_id)                                             AS total_kills,
    ROUND(COUNT(k.kill_id) / NULLIF(COUNT(DISTINCT m.match_id), 0), 1) AS kills_per_match
FROM map AS mp
JOIN game AS g           ON g.game_id = mp.game_id
LEFT JOIN `match` AS m   ON m.map_id = mp.map_id
LEFT JOIN kill_table AS k ON k.match_id = m.match_id
GROUP BY mp.map_id, mp.name, g.name, mp.size_category, mp.design_style;

-- Statistici per armă: kill-uri, headshot-uri și procentul de headshot.
-- LEFT JOIN: arma neutilizată apare cu 0 kill-uri.
CREATE OR REPLACE VIEW v_weapon_stats AS
SELECT
    w.weapon_id,
    w.name         AS weapon_name,
    w.category,
    COUNT(k.kill_id)                       AS total_kills,
    COALESCE(SUM(k.is_headshot), 0)        AS headshots,
    ROUND(100 * COALESCE(SUM(k.is_headshot), 0) / NULLIF(COUNT(k.kill_id), 0), 1) AS headshot_pct
FROM weapon AS w
LEFT JOIN kill_table AS k ON k.weapon_id = w.weapon_id
GROUP BY w.weapon_id, w.name, w.category;

-- Statistici per arhetip (doar jucătorii care au jucat). Răspunde la „cât de diferite sunt arhetipurile?".
CREATE OR REPLACE VIEW v_archetype_stats AS
SELECT
    archetype,
    COUNT(*)                                          AS players,
    SUM(matches_played)                               AS matches_played,
    SUM(total_kills)                                  AS total_kills,
    SUM(total_deaths)                                 AS total_deaths,
    ROUND(SUM(total_kills) / NULLIF(SUM(total_deaths), 0), 2) AS kd_ratio
FROM v_player_stats
GROUP BY archetype;
