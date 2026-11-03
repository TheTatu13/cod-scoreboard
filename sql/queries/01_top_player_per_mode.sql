-- Întrebare: cine e cel mai bun jucător (după K/D) pe fiecare mod de joc?
-- Condiție: minim 5 meciuri în modul respectiv, ca să nu câștige cineva cu 1 meci norocos.
-- Tehnică: CTE (WITH) + funcție fereastră ROW_NUMBER() împărțită pe mod (PARTITION BY).
WITH per_mode AS (
    SELECT
        m.mode,
        p.gamertag,
        COUNT(*)                                            AS matches,
        SUM(mp.kills)                                       AS kills,
        SUM(mp.deaths)                                      AS deaths,
        ROUND(SUM(mp.kills) / NULLIF(SUM(mp.deaths), 0), 2) AS kd
    FROM match_player AS mp
    JOIN `match` AS m ON m.match_id = mp.match_id
    JOIN player  AS p ON p.player_id = mp.player_id
    GROUP BY m.mode, mp.player_id, p.gamertag
    HAVING COUNT(*) >= 5
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY mode ORDER BY kd DESC, kills DESC) AS rn
    FROM per_mode
)
SELECT mode, gamertag, matches, kills, deaths, kd
FROM ranked
WHERE rn = 1
ORDER BY mode;
