# COD Scoreboard

> Platformă de date batch construită în jurul unui simulator de meciuri Call of Duty.
> Generator de date sintetice cu defecte controlate → MySQL (sursă) → pipeline ELT în
> PostgreSQL (dbt, Airflow) → dashboard și API.

**Stare:** în lucru (săptămânile 1–3 din 13 gata: generator, teste, feed cu defecte). Roadmap complet: [`docs/ROADMAP.md`](docs/ROADMAP.md).

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
sql/schema/       schema MySQL (rulată automat de Docker)
sql/queries/      interogări analitice, fiecare cu întrebarea de business
tests/            teste (invarianți pe date, smoke)
docs/             roadmap, calitatea datelor, ERD, data dictionary, optimizări
.github/workflows CI (ruff + pytest)
```

## Date sintetice

Datele sunt generate de un simulator (5.000 de jucători, dintre care 500 activi în meciuri,
1000 de meciuri, ~60.000 de kill-uri). Arhetipurile de jucători (9 planificate) sunt în lucru.
Defectele sunt injectate intenționat și nu reprezintă date reale.

## Ce urmează

- [ ] Fundația: Docker, generator cu `--seed`, teste, CI (`docs/WEEKS-1-2.md`)
- [ ] Generator ca sistem-sursă, cu defecte controlate
- [ ] Ingestie incrementală și idempotentă
- [ ] dbt: staging, marts, teste
- [ ] Airflow, dashboard, API
