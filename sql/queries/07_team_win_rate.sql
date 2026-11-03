-- Întrebare: ce echipă câștigă mai des, pe fiecare mod de joc? (verifică și corectitudinea simulării)
-- Tehnică: JOIN pe team, COUNT condiționat.
SELECT
    m.mode,
    t.name                                                    AS winner_team,
    COUNT(*)                                                  AS wins,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY m.mode), 1) AS pct_of_mode
FROM `match` AS m
JOIN team AS t ON t.team_id = m.winner_team_id
GROUP BY m.mode, t.name
ORDER BY m.mode, wins DESC;
