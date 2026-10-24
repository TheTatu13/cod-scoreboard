# Săptămânile 1-2: fundația

Scris după ce am citit scripturile tale reale (folderul „Call of Duty Scoreboard"). Ordinea
contează. Fiecare task are un criteriu „gata când". Codul îl scrii tu; când te blochezi,
trimite eroarea exactă și ce ai încercat.

## T0. Scoate parola din cod (înainte de orice commit)

Parola MySQL e scrisă în clar în toate scripturile (`simulate_matches.py`, `seed_player.py`,
`match_seed.py`, `kill_events.py`, `match_player_seed.py`, `test_conexiune.py`). Dacă le comiți
așa, ajunge în istoricul Git și rămâne acolo chiar dacă o ștergi mai târziu.

1. Copiază `.env.example` în `.env` și pune parola acolo (`.env` e deja în `.gitignore`).
2. În scripturi, înlocuiește `mysql.connector.connect(host=..., password="...")` cu
   `from cod.db import get_connection` și `conn = get_connection()`.
3. Schimbă parola root a MySQL-ului tău local, ca să nu mai coincidă cu cea din fișierele vechi
   (și dacă ai folosit-o și în alt loc).

Gata când: `grep -ri "password" src/` nu mai arată nicio parolă.

## T1. Repo și Git (ziua 1-2)

```bash
cd cod-scoreboard
git init -b main
git config user.name "Mihai"
git config user.email "ID+USERNAME@users.noreply.github.com"   # GitHub → Settings → Emails
git add .
git commit -m "Scheletul proiectului"
git switch -c feat/foundation
```

Creează repo-ul pe GitHub, public abia după T0. Apoi `git remote add origin ...` și
`git push -u origin main`.

Gata când: `git log --oneline` arată commit-uri mici și clare, iar `.env` nu apare în `git status`.

## T2. Schema în repo (ziua 2-3)

`sql/Cod_ScoreBoard.sql` din folderul tău conține doar o interogare, nu schema. Mută-l în
`sql/queries/jucatori_15_meciuri.sql`. Schema (CREATE TABLE) există doar în baza ta, deci
exportă-o (comanda e în `sql/schema/README.md`) în `sql/schema/01_schema.sql`. Dacă
`mysqldump` nu e în PATH în Git Bash, folosește Workbench: Server → Data Export →
„Export to Self-Contained File", cu „Dump Structure Only".

Copiază `.env.example` în `.env`. Apoi:

```bash
docker compose up -d
docker compose exec mysql mysql -uroot -p cod_scoreboard -e "SHOW TABLES;"
```

Gata când: vezi cele 9 tabele într-un container pornit de la zero
(`docker compose down -v && docker compose up -d`). Necesită Docker Desktop.

## T3. Generatorul în repo, parametrizat (ziua 3-6)

Punctul de pornire e `simulate_matches.py` (cel mai bun script al tău: simulează kill-urile
în memorie, deduce câștigătorul din ele și calculează match_player din aceleași evenimente).

1. Mută-l în `src/cod/generator/simulate.py` și pune codul într-o funcție
   `main(seed, matches, pool_size, reset)`, nu la nivel de modul.
2. Adaugă `argparse`: `--seed`, `--matches` (acum 1000), `--pool` (acum 500), `--reset`.
3. Conexiunea vine din `get_connection()` (T0).
4. `--reset`: golește `kill_table`, `match_player`, `match` (în ordinea FK-urilor) înainte de
   inserare. Acum, dacă rulezi scriptul de 2 ori, ai 2000 de meciuri. Nu e idempotent.

Gata când: `python -m cod.generator.simulate --seed 42 --reset` rulează fără alte intervenții,
iar o a doua rulare dă același număr de rânduri.

## T4. Determinism (ziua 6-7)

Acum același rezultat nu se poate reproduce din două motive:

- folosești `random.xxx(...)` global (`sample`, `choices`, `uniform`, `randint`);
- `started_at` se calculează din `datetime.now()`.

Rezolvare: creează `rng = random.Random(seed)` la început și înlocuiește fiecare `random.`
cu `rng.`; calculează `started_at` dintr-o dată de bază fixă (`--date`, ex. 2026-01-01),
nu din `now()`. La `seed_player.py` la fel, iar `fake = Faker()` e creat dar nefolosit: scoate-l.

Gata când: rulezi de 2 ori cu același seed, pe baze goale, și `SELECT COUNT(*)`, `SUM(kills)`
și `MIN(started_at)` dau exact aceleași valori.

## T4b. Scripturile vechi (ziua 7)

`match_seed.py`, `kill_events.py` și `match_player_seed.py` sunt prima ta abordare, înlocuită
de `simulate_matches.py`. Mută-le în `legacy/` sau șterge-le (istoricul Git le păstrează).
Au și un bug util pentru T5: `kill_events.py` dă `timestamp_in_match = randint(0, 600)`, dar
durata meciului e între 300 și 900 secunde, deci poți avea kill-uri după sfârșitul meciului.
`simulate_matches.py` nu are bugul (`randint(0, duration)`). Transformă-l în test: primul tău
invariant care ar fi prins greșeala.

## T5. Teste de invarianți (ziua 7-11)

Completează `tests/test_invariants.py`: cele 5 stub-uri, apoi până la 10-15 teste. Fiecare test
e o interogare SQL scrisă de tine care caută ceva ce NU are voie să existe, plus `assert ... == 0`.
Idei specifice datelor tale: killer și victim din echipe diferite; assister din aceeași echipă cu
killer; `match_player.kills` = numărul din `kill_table`; `winner_team_id` e echipa cu mai multe
kill-uri (la egalitate e aleasă la întâmplare, deci tratează cazul); `score = kills*100 +
assists*50`; fiecare meci are exact 12 jucători.

Gata când: `pytest -q` arată 10+ teste trecute (nu sărite) pe baza populată.

## T6. CI verde (ziua 11-12)

Push pe GitHub, verifică tab-ul Actions. Adaugă badge-ul în README.
Gata când: workflow-ul `CI` e verde pe `main`. În CI nu există încă bază de date, deci testele
care cer `db` sunt sărite acolo; se rezolvă în săptămâna 10, cu un service MySQL în workflow.

## T7. Faza 2, doar esențialul (ziua 11-13)

- 5-8 interogări analitice în `sql/queries/` (CTE, window functions), fiecare cu întrebarea de
  business în comentariu. Cele două din chatul nostru (hărți după media de kills, platforme)
  pot intra, rescrise de tine.
- `EXPLAIN` înainte/după pentru 2-3 indexuri, cu timpii măsurați, în `docs/optimization/`.
- ERD și data dictionary în `docs/`.
Stored procedure e opțională: apare rar în anunțurile de DE junior.

## T8. README v1 (ziua 13-14)

Completează toate `TODO`-urile din README: problema, arhitectura țintă, cum pornești proiectul
în 3 comenzi, ce e gata și ce urmează. Atribuirea celor 9 arhetipuri e încă în lucru (acum toți
jucătorii sunt „Recrut"), deci scrie asta onest în README.

## Ce NU faci acum

Airflow, dbt, Postgres, Spark, Kafka. Vin la rând, în ordinea din `ROADMAP.md`.

---

## Status (generat de Claude)

Făcut și verificat pe schema ta REALĂ (`sql/schema/01_schema.sql`, exportată din MySQL-ul tău), încărcată într-o bază de probă:
- generatorul: `python -m cod.generator --seed 42 --reset` (fără parolă în cod, citește `.env`);
- determinism: același seed → aceleași date; idempotență: fără `--reset` refuză pe tabele pline;
- arhetipurile sunt atribuite (K/D mediu: Demon ~2+, Recrut ~0.8) și influențează simularea;
- 30 de teste trec (15 pe simulare fără DB, 15 invarianți SQL);
- testele pe schema reală au prins un bug: `gamertag` e VARCHAR(25), iar generatorul făcea nume mai lungi. Reparat.

Rămâne la tine:
1. Scoate parola din scripturile vechi și schimb-o (a fost în cod).
2. `git init`, commit-uri, push.
3. Valorile din `src/cod/generator/archetypes.py` sunt alegerea mea de pornire: ajustează-le.
