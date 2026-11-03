# COD Scoreboard

> Platformă de date batch construită în jurul unui simulator de meciuri Call of Duty.
> Generator de date sintetice cu defecte controlate → MySQL (sursă) → pipeline ELT în
> PostgreSQL (dbt, Airflow) → dashboard și API.

**Stare:** în lucru (săptămânile 1–3 din 13 gata: generator, teste, feed cu defecte; plus views și query-uri analitice, Faza 2, și ingestia în PostgreSQL, Faza 3). Roadmap complet: [`docs/ROADMAP.md`](docs/ROADMAP.md).

![CI](https://github.com/TheTatu13/cod-scoreboard/actions/workflows/ci.yml/badge.svg)

## Problema

Proiectul simulează 1.500 de meciuri Call of Duty între 15.000 de jucători, cu arme, hărți și
arhetipuri de jucători care influențează rezultatele (K/D mediu de la sub 1 la peste 2). Din date
trebuie să poți afla ce hartă dă cele mai multe kill-uri, cine e cel mai bun jucător pe un mod de
joc și cum se compară armele. Datele reale vin murdare (duplicate, evenimente întârziate, ID-uri
inexistente, scheme schimbate), așa că proiectul le injectează controlat și verifică, cu un
manifest ca adevăr de comparat, că pipeline-ul le prinde pe toate.

## Arhitectura țintă

```
generator → MySQL (OLTP) + fișiere JSON
          → Airflow → PostgreSQL (raw → staging → marts) ← dbt + teste
          → dashboard + API FastAPI
```

Detalii în [`docs/ROADMAP.md`](docs/ROADMAP.md). Planul de calitate a datelor:
[`docs/DATA-QUALITY.md`](docs/DATA-QUALITY.md).

## Pornire rapidă

Necesită Python 3.12 (merge și 3.14) și MySQL 8, fie în Docker, fie instalat local.

```bash
cp .env.example .env            # apoi pune propria parolă în .env
pip install -r requirements.txt
```

**Cu Docker:** `docker compose up -d` pornește MySQL pe portul 3307 și încarcă schema automat.

**Fără Docker (MySQL local):** creează o bază separată și încarcă schema din
`sql/schema/01_schema.sql`, apoi pune în `.env`: `MYSQL_DATABASE=cod_dev` și `MYSQL_HOST_PORT=3306`.

Apoi (PowerShell: `$env:PYTHONPATH="src"`; bash: `export PYTHONPATH=src`):

```bash
python -m cod.generator --seed 42 --reset      # golește tabelele și generează datele
python -m cod.generator.events --seed 42       # feed-ul JSON cu defecte, în data/events/
pytest -q                                      # teste pe simulare, pe date și pe defecte
```

Același seed produce exact aceleași date. `--reset` golește toate tabelele din baza din `.env`.

## Structura

```
src/cod/          cod Python (conexiune DB, generator, ingestie)
sql/warehouse/    schema raw din PostgreSQL (rulată de `cod.ingest`)
sql/schema/       schema MySQL (rulată automat de Docker)
sql/queries/      interogări analitice, fiecare cu întrebarea de business
tests/            teste (invarianți pe date, smoke)
docs/             roadmap, calitatea datelor, ERD, data dictionary, optimizări
.github/workflows CI (ruff + pytest)
```

## Ingestia în PostgreSQL

Pornește și PostgreSQL (`docker compose up -d` pornește ambele baze, portul 5433), apoi:

```bash
python -m cod.generator.events --seed 42 --out data/events   # feed-ul JSON cu defecte
python -m cod.ingest                                         # MySQL + JSON -> PostgreSQL raw
```

Incrementală (watermark) și idempotentă: aceeași zi de două ori dă aceleași rânduri. Detalii și
verificarea pe manifestul de defecte: [`docs/INGESTIE.md`](docs/INGESTIE.md).

## Views și query-uri analitice

Views (`sql/schema/02_views.sql`): `v_player_stats`, `v_map_stats`, `v_weapon_stats`,
`v_archetype_stats` (plus `v_player_leaderboard`, în schema de bază). Query-urile din
`sql/queries/`, fiecare cu întrebarea de business în primele rânduri:

| Fișier | Întrebare |
|---|---|
| `01_top_player_per_mode` | Cel mai bun jucător (K/D) pe fiecare mod de joc |
| `02_maps_by_kills_per_match` | Hărțile cu cele mai multe kill-uri pe meci |
| `03_weapon_categories` | Compararea categoriilor de arme (kill-uri, headshot) |
| `04_archetype_comparison` | Cât influențează arhetipul K/D-ul |
| `05_inactive_players` | Câți jucători nu au jucat niciun meci |
| `06_unused_weapons` | Arme fără niciun kill (ar fi un semnal în generator) |
| `07_team_win_rate` | Ce echipă câștigă mai des, pe mod |
| `08_monthly_activity` | Meciuri și kill-uri pe lună |
| `09_top_headshot_players` | Cel mai mare procent de headshot (min. 100 kill-uri) |

Două indexuri acoperitoare (`sql/schema/03_indexes.sql`), cu măsurătorile din
[`docs/optimization/faza-2-indexuri.md`](docs/optimization/faza-2-indexuri.md).
Testele din `tests/test_views.py` compară fiecare view cu un calcul independent pe tabelele de bază.

## Date sintetice

Datele sunt generate de un simulator (implicit 15.000 de jucători, dintre care 500 activi în meciuri,
1.500 de meciuri, ~89.000 de kill-uri). Arhetipurile de jucători (9, plus `Recrut` ca valoare
implicită) influențează K/D-ul. Defectele sunt injectate intenționat și nu reprezintă date reale.

## Ce urmează

- [ ] Fundația: Docker, generator cu `--seed`, teste, CI (`docs/WEEKS-1-2.md`)
- [ ] Generator ca sistem-sursă, cu defecte controlate
- [x] Ingestie incrementală și idempotentă
- [ ] dbt: staging, marts, teste
- [ ] Airflow, dashboard, API
