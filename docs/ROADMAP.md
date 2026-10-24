# Roadmap: Varianta A (platformă de date batch, ~13 săptămâni)

Obiectiv: COD Scoreboard devine un pipeline ELT complet, rulat zilnic, cu calitatea datelor
verificată, și un API subțire la final. Ținta: primul job în Data Engineering, deschis și la
Backend/QA.

Estimările de timp sunt ale mele (1-2 ore/zi). La 1 oră/zi, ia capătul de sus al intervalelor.
Ordinea contează mai mult decât durata: nu începi o etapă până nu e verde cea dinainte.

## Arhitectura țintă

```
generator (--seed, --date, chaos config)
   │ scrie zilnic
   ▼
MySQL (OLTP, sursa jocului)  +  fișiere JSON de evenimente
   │ ingestie incrementală, idempotentă (Airflow)
   ▼
PostgreSQL: raw → staging → marts (schemă star)   ← dbt Core 1.x + teste
   │                         └→ rejected_* (carantină) + raport de reconciliere
   ▼
dashboard (Metabase/Streamlit)  +  API FastAPI read-only (la final)
```

Decizii (opinie argumentată în raportul de cercetare):
- MySQL rămâne baza operațională a jocului. Warehouse-ul e în PostgreSQL, fiindcă adaptorul
  dbt-mysql e întreținut de comunitate și fără suport oficial.
- Fixează dbt Core 1.x (`requirements.txt`), nu urmări upgrade-uri în timpul proiectului.
- Airflow cu LocalExecutor în Docker Compose. Fără Spark, Kafka sau Terraform: la ~60k de
  rânduri nu aduc nimic și îți fragmentează timpul.

## Etape

| Săpt. | Livrabil | Gata când |
|---|---|---|
| 1-2 | Fundația: repo public, Docker (MySQL), generator cu `--seed`, 10-15 teste, CI, README v1 (vezi `WEEKS-1-2.md`) | `docker compose up -d` și `pytest` trec local și în GitHub Actions |
| 3 | Generatorul ca sistem-sursă: partiții zilnice + chaos config (vezi `DATA-QUALITY.md`) | `generate --date D --seed S` dă același rezultat la fiecare rulare; erorile injectate sunt numărate în log |
| 4 | Ingestie: MySQL + JSON → Postgres `raw`, incremental (watermark), idempotentă | rulezi aceeași zi de 2 ori și numărul de rânduri rămâne identic |
| 5-6 | dbt: sources, staging, marts (star: `fct_kill_event`, `fct_player_match`, `dim_*`), teste, docs, snapshot SCD2 pe `dim_player` | `dbt build` verde; `dbt docs` arată lineage-ul |
| 7 | Calitate: `rejected_*`, raport zilnic „citit = încărcat + respins", dashboard de calitate | nicio diferență nejustificată în raport, pe 30 de zile |
| 8 | Airflow: DAG zilnic, retry-uri, alertă la eșec, backfill 30 de zile | backfill-ul de 30 de zile rulează fără intervenție manuală |
| 9 | Serving: dashboard (leaderboard, arme/hărți, calitate date) + rating OpenSkill | dashboard-ul rulează din `docker compose up` |
| 10 | CI complet: ruff + pytest + `dbt build` pe Postgres efemer, la fiecare PR | un PR cu o eroare e blocat de CI |
| 11-12 | API slice FastAPI (leaderboard, profil jucător), paginare, pytest + 3-5 teste Playwright | endpoint-urile și testele rulează în CI |
| 13 | Prezentare: README final, ERD (OLTP + warehouse), video demo 2-3 min, post LinkedIn, bullet-uri CV | cineva străin pornește proiectul în sub 5 minute |

## Aplicații la joburi

Începe din săptămâna 4-5, cu proiectul în lucru și README-ul la zi. Piața de juniori din
România e strânsă, deci aplică în paralel și la QA automation și la tech support cu SQL.

## Reguli de lucru

- Un branch per etapă (`feat/ingestie`, `feat/dbt`...), PR către `main`, chiar dacă lucrezi singur.
- Commit-uri mici, cu mesaje clare. Fără parole în repo.
- README-ul se actualizează la fiecare etapă, nu la final.
- Dacă o etapă depășește de 2 ori estimarea, simplifică ținta, nu adăuga ore.
