# Faza 2: două indexuri acoperitoare pe `kill_table`

Date: seed 42, 89.427 kill-uri, MySQL 8.0. Timpii sunt intervale din 5 rulări `EXPLAIN ANALYZE`,
măsurate pe aceeași bază cu indexul forțat (`USE INDEX`) sau ignorat (`IGNORE INDEX`). Variază de la
o rulare la alta; contează diferența de plan, nu cifra exactă.

## Problema

`kill_table` e tabela mare. Două interogări o parcurg integral pentru a număra kill-uri și headshot-uri:

1. `v_weapon_stats`: `GROUP BY weapon_id` cu `SUM(is_headshot)`
2. `09_top_headshot_players.sql`: `GROUP BY killer_id` cu `SUM(is_headshot)`

Cu indexurile existente (câte unul pe `weapon_id`, respectiv `killer_id`), MySQL găsea rândurile
prin index, dar trebuia să se întoarcă în tabel după `is_headshot`.

## Înainte

| Interogare | Plan | Timp |
|---|---|---|
| per armă | `Index scan on kill_table using weapon_id` | 89–115 ms |
| per jucător | fără indexul acoperitor (`Table scan on k`, în prima măsurare) | 168–183 ms |

## Indexul

```sql
ALTER TABLE kill_table ADD INDEX idx_kill_weapon_headshot (weapon_id, is_headshot);
ALTER TABLE kill_table ADD INDEX idx_kill_killer_headshot (killer_id, is_headshot);
```

Un index care conține **toate coloanele de care are nevoie interogarea** se numește acoperitor
(covering): MySQL răspunde doar din index, fără să atingă tabelul.

## După

| Interogare | Plan | Timp |
|---|---|---|
| per armă | `Covering index scan using idx_kill_weapon_headshot` | 20–22 ms (de ~4–5 ori mai rapid) |
| per jucător | `Covering index scan on k using idx_kill_killer_headshot` | 102–106 ms (~40% mai rapid) |

## Costuri și limite

- Fiecare index ocupă loc și încetinește `INSERT`-urile pe `kill_table`. Aici datele se scriu în
  loturi la generare, deci costul e mic. Într-un sistem cu scrieri continue ar trebui măsurat.
- `idx_kill_weapon_headshot` face redundant indexul vechi doar pe `weapon_id` (aceeași coloană
  în față). Nu l-am șters, fiindcă e creat automat pentru cheia străină și nu am vrut să
  schimb schema originală în această etapă.
- La 89 de mii de rânduri câștigul e de milisecunde. Contează ca tipar, nu ca urgență.
