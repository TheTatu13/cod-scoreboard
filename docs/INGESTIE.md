# Ingestia (Faza 3): MySQL + JSON → PostgreSQL `raw`

```
MySQL (game, map, weapon, weapon_game, team, player, match, match_player) ──┐
                                                                            ├─► PostgreSQL, schema raw
data/events/dt=<zi>/kills.jsonl (feed cu defecte) ──────────────────────────┘
```

Comenzi (din rădăcina repo-ului, cu `PYTHONPATH=src`):

```bash
python -m cod.generator.events --seed 42 --out data/events   # feed-ul JSON
python -m cod.ingest                                         # incremental: zilele după watermark
python -m cod.ingest --day 2025-03-05                        # o zi anume
python -m cod.ingest --from 2025-01-01 --to 2025-01-31       # backfill pe interval
```

## Ce e „raw" și ce nu e

Raw e o copie fidelă a sursei. Nu corectează, nu șterge duplicate, nu pune chei străine. Un rând
stricat în sursă trebuie să fie stricat și în raw: curățarea e treaba stratului `staging` (dbt,
săptămânile 5–6). Dacă raw ar „repara" datele, n-ai mai ști ce a trimis sursa de fapt.

Feed-ul se păstrează ca `payload jsonb`, exact cum a venit. De aceea schimbarea de schemă din feed
(`is_headshot` → `headshot`, apare `client_version`) nu strică încărcarea.

## Idempotența: aceeași zi de două ori = aceleași rânduri

| Sursă | Tehnică |
|---|---|
| tabelele din MySQL | `INSERT ... ON CONFLICT (cheia primară) DO UPDATE` (upsert) |
| feed JSON | suprascrierea partiției: `DELETE` ziua + `COPY` ziua, în aceeași tranzacție |

Fiecare zi dintr-o sursă e o singură tranzacție: se încarcă complet sau deloc. Dacă pică ceva la
mijloc, se face rollback, iar în `ingest_run` rămâne un rând cu `status = 'failed'`.

## Incremental: watermark

`ingest_watermark` ține, pentru fiecare sursă (`feed.kills`, `mysql.match`), ultima zi încărcată
cu succes. Fără argumente, `cod.ingest` procesează doar zilele mai noi. Watermark-ul nu merge
niciodată înapoi: dacă re-rulezi o zi veche cu `--day`, rămâne la valoarea mai mare.

Feed-ul se partiționează pe **ziua de livrare**, nu pe ziua evenimentului. Un eveniment întârziat
ajunge deci în partiția zilei în care a sosit, iar watermark-ul rămâne corect.

## Reconcilierea la ingestie

Pentru fiecare zi de feed: `rânduri citite = încărcate + respinse`, altfel rularea eșuează.
Liniile care nu sunt JSON valid (sau nu sunt obiecte) merg în `kill_event_rejected`, cu eroarea.
Nu se pierd și nu opresc rularea. `ingest_run` ține cifrele pe fiecare rulare.

## Verificat pe manifest (seed 42)

Generatorul scrie `_manifest.json` cu adevărul. Testele din `tests/test_ingest.py` compară raw cu el:

| Verificare | Rezultat |
|---|---|
| rânduri emise de generator = rânduri în `raw.kill_event` | 91.169 = 91.169 |
| evenimente distincte = evenimente curate | 89.427 |
| duplicatele sunt păstrate | 1.742 |
| evenimentele întârziate stau în partiția de livrare, nu în ziua lor | corect |
| rândurile cu schema schimbată au `headshot`, nu `is_headshot` | corect |
| victimele inexistente (457) sunt încă în raw, necorectate | corect |
| `player`, `match`, `match_player` = numărul de rânduri din MySQL | 15.000 / 1.500 / 18.000 |

O încărcare completă durează ~5 secunde.

## Limite cunoscute

- **Meciurile se încarcă după `started_at`.** Un meci modificat sau adăugat retroactiv, într-o zi
  deja trecută de watermark, nu e prins în modul incremental. Rezolvare: `--day` sau `--from/--to`.
- **Ștergerile din MySQL nu se propagă.** Upsert-ul nu șterge rândurile dispărute din sursă.
  Jocul nu șterge meciuri, deci e acceptabil aici.
- **Tabelele de referință se copiază integral** la fiecare rulare (15.373 de rânduri). Sunt mici
  și nu au coloană `updated_at`, deci n-ar avea după ce să filtreze.
- Testate pe PostgreSQL 16 și MySQL 8.0 instalate local. Serviciul `postgres` din
  `docker-compose.yml` n-a fost rulat încă.
