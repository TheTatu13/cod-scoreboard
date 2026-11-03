-- Întrebare: cum evoluează activitatea lună de lună (meciuri, kill-uri, kill-uri pe meci)?
-- Tehnică: DATE_FORMAT pentru a grupa pe lună; kill-urile se agregă întâi pe meci, apoi pe lună,
-- ca să nu înmulțim rândurile (JOIN direct match -> kill_table ar funcționa, dar e mai lent).
WITH kills_per_match AS (
    SELECT match_id, COUNT(*) AS kills FROM kill_table GROUP BY match_id
)
SELECT
    DATE_FORMAT(m.started_at, '%Y-%m')           AS month,
    COUNT(*)                                     AS matches,
    SUM(COALESCE(kpm.kills, 0))                  AS kills,
    ROUND(AVG(COALESCE(kpm.kills, 0)), 1)        AS kills_per_match
FROM `match` AS m
LEFT JOIN kills_per_match AS kpm ON kpm.match_id = m.match_id
GROUP BY DATE_FORMAT(m.started_at, '%Y-%m')
ORDER BY month;
