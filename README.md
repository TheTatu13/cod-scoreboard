# COD Scoreboard

> Platformă de date batch construită în jurul unui simulator de meciuri Call of Duty.
> Generator de date sintetice cu defecte controlate → MySQL (sursă) → pipeline ELT în
> PostgreSQL (dbt, Airflow) → dashboard și API.

**Stare:** în lucru (săptămâna 1 din 13). Roadmap complet: [`docs/ROADMAP.md`](docs/ROADMAP.md).

<!-- badge CI: adaugă după primul push, formatul e în tab-ul Actions → Create status badge -->

## Problema

TODO (3 propoziții, cu vorbele tale): ce simulează proiectul, ce întrebări analitice
trebuie să poată răspunde (ex. cine e cel mai bun jucător pe Hardpoint, ce hartă dă cele mai
multe kill-uri) și de ce datele trebuie validate.

## Arhitectura țintă

```
generator → MySQL (OLTP) + fișiere JSON
          → Airflow → PostgreSQL (raw → staging → marts) ← dbt + teste
          → dashboard + API FastAPI
```

Detalii în [`docs/ROADMAP.md`](docs/ROADMAP.md). Planul de calitate a datelor:
[`docs/DATA-QUALITY.md`](docs/DATA-QUALITY.md).

## Pornire rapidă

Necesită Docker Desktop și Python 3.12.

```bash
cp .env.example .env            # apoi pune propria parolă în .env
docker compose up -d            # MySQL pe portul 3307, schema încărcată automat
pip install -r requirements.txt && pytest -q
```

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
