"""Încărcătoarele: fiecare funcție încarcă O zi dintr-o sursă, într-o singură tranzacție.

Idempotența vine din două tehnici:
  * tabelele din MySQL: upsert pe cheia primară (INSERT ... ON CONFLICT DO UPDATE)
  * feed-ul JSON: suprascrierea partiției (DELETE zi + COPY zi, în aceeași tranzacție)
Rulezi aceeași zi de două ori și rămân exact aceleași rânduri.
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DDL_FILE = Path(__file__).resolve().parents[3] / "sql" / "warehouse" / "01_raw.sql"

# tabel MySQL -> (coloane, cheia primară). `match` e cuvânt rezervat în MySQL: ghilimele inverse.
REFERENCE_TABLES = {
    "game": (["game_id", "name", "release_year", "studio"], ["game_id"]),
    "map": (["map_id", "name", "game_id", "size_category", "design_style", "image_url"],
            ["map_id"]),
    "weapon": (["weapon_id", "name", "category"], ["weapon_id"]),
    "weapon_game": (["weapon_id", "game_id"], ["weapon_id", "game_id"]),
    "team": (["team_id", "name"], ["team_id"]),
    "player": (["player_id", "gamertag", "platform", "created_at", "archetype"], ["player_id"]),
}
MATCH_COLS = ["match_id", "map_id", "mode", "started_at", "duration_sec", "winner_team_id"]
MATCH_PLAYER_COLS = ["match_id", "player_id", "team_id", "kills", "deaths", "assists", "score"]

SRC_KILLS = "feed.kills"
SRC_MATCH = "mysql.match"


@dataclass
class RunResult:
    source: str
    day: date
    rows_read: int
    rows_loaded: int
    rows_rejected: int = 0


def ensure_schema(pg) -> None:
    """Creează tabelele din `raw` dacă lipsesc (idempotent)."""
    with pg.cursor() as cur:
        cur.execute(DDL_FILE.read_text(encoding="utf-8"))
    pg.commit()


def _upsert(pg, table: str, cols: list[str], pk: list[str], rows: list[tuple]) -> None:
    if not rows:
        return
    placeholders = ", ".join(["%s"] * len(cols))
    non_pk = [c for c in cols if c not in pk]
    sets = ", ".join([f"{c} = EXCLUDED.{c}" for c in non_pk] + ["_ingested_at = now()"])
    sql = (f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
           f"ON CONFLICT ({', '.join(pk)}) DO UPDATE SET {sets}")
    with pg.cursor() as cur:
        cur.executemany(sql, rows)


def load_reference(my, pg) -> dict[str, int]:
    """Copie completă (upsert) a tabelelor mici de referință. Returnează rânduri pe tabel."""
    counts = {}
    cursor = my.cursor()
    for table, (cols, pk) in REFERENCE_TABLES.items():
        cursor.execute(f"SELECT {', '.join(cols)} FROM `{table}`")
        rows = cursor.fetchall()
        _upsert(pg, table, cols, pk, rows)
        counts[table] = len(rows)
    cursor.close()
    pg.commit()
    return counts


def _start_run(pg, source: str, day: date) -> int:
    with pg.cursor() as cur:
        cur.execute("INSERT INTO ingest_run (source, day) VALUES (%s, %s) RETURNING run_id",
                    (source, day))
        return cur.fetchone()[0]


def _finish_run(pg, run_id: int, source: str, day: date, res: RunResult) -> None:
    with pg.cursor() as cur:
        cur.execute(
            "UPDATE ingest_run SET finished_at = now(), status = 'ok', rows_read = %s, "
            "rows_loaded = %s, rows_rejected = %s WHERE run_id = %s",
            (res.rows_read, res.rows_loaded, res.rows_rejected, run_id))
        cur.execute(
            "INSERT INTO ingest_watermark (source, last_day) VALUES (%s, %s) "
            "ON CONFLICT (source) DO UPDATE SET "
            "last_day = GREATEST(ingest_watermark.last_day, EXCLUDED.last_day), updated_at = now()",
            (source, day))


def _record_failure(pg, source: str, day: date) -> None:
    """După rollback: lasă o urmă că rularea a eșuat (într-o tranzacție separată)."""
    with pg.cursor() as cur:
        cur.execute("INSERT INTO ingest_run (source, day, finished_at, status) "
                    "VALUES (%s, %s, now(), 'failed')", (source, day))
    pg.commit()


def get_watermark(pg, source: str) -> date | None:
    with pg.cursor() as cur:
        cur.execute("SELECT last_day FROM ingest_watermark WHERE source = %s", (source,))
        row = cur.fetchone()
    return row[0] if row else None


def load_matches(my, pg, day: date) -> RunResult | None:
    """Meciurile începute în `day` și rândurile lor din match_player. None dacă nu sunt."""
    cursor = my.cursor()
    cursor.execute(f"SELECT {', '.join(MATCH_COLS)} FROM `match` WHERE DATE(started_at) = %s",
                   (day,))
    matches = cursor.fetchall()
    if not matches:
        cursor.close()
        return None
    ids = [m[0] for m in matches]
    marks = ", ".join(["%s"] * len(ids))
    cursor.execute(f"SELECT {', '.join(MATCH_PLAYER_COLS)} FROM match_player "
                   f"WHERE match_id IN ({marks})", ids)
    players = cursor.fetchall()
    cursor.close()
    try:
        run_id = _start_run(pg, SRC_MATCH, day)
        _upsert(pg, "match", MATCH_COLS, ["match_id"], matches)
        _upsert(pg, "match_player", MATCH_PLAYER_COLS, ["match_id", "player_id"], players)
        res = RunResult(SRC_MATCH, day, len(matches) + len(players), len(matches) + len(players))
        _finish_run(pg, run_id, SRC_MATCH, day, res)
        pg.commit()
    except Exception:
        pg.rollback()
        _record_failure(pg, SRC_MATCH, day)
        raise
    return res


def partition_days(events_dir: Path) -> list[date]:
    """Zilele de livrare pentru care există o partiție `dt=YYYY-MM-DD/kills.jsonl`."""
    days = []
    for part in events_dir.glob("dt=*"):
        if (part / "kills.jsonl").is_file():
            days.append(date.fromisoformat(part.name.removeprefix("dt=")))
    return sorted(days)


def _parse_lines(path: Path):
    """Generează (line_no, payload_text, event_id) sau (line_no, line, error)."""
    with open(path, encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError("linia nu e un obiect JSON")
            except ValueError as exc:
                yield line_no, line, str(exc), True
                continue
            event_id = obj.get("event_id")
            yield line_no, line, None if event_id is None else str(event_id), False


def load_kills(pg, events_dir: Path, day: date) -> RunResult | None:
    """Încarcă partiția dt=<day>, suprascriind-o. None dacă partiția nu există."""
    path = events_dir / f"dt={day.isoformat()}" / "kills.jsonl"
    if not path.is_file():
        return None
    try:
        run_id = _start_run(pg, SRC_KILLS, day)
        with pg.cursor() as cur:
            cur.execute("DELETE FROM kill_event WHERE dt = %s", (day,))
            cur.execute("DELETE FROM kill_event_rejected WHERE dt = %s", (day,))
            read = loaded = 0
            bad_rows = []
            # O singură operație COPY pe conexiune la un moment dat: liniile bune merg prin COPY,
            # cele respinse (rare) se adună și se inserează după ce COPY s-a terminat.
            with cur.copy("COPY kill_event (dt, line_no, event_id, payload, source_file, run_id) "
                          "FROM STDIN") as copy:
                for line_no, text, extra, is_bad in _parse_lines(path):
                    read += 1
                    if is_bad:
                        bad_rows.append((day, line_no, text, extra, str(path), run_id))
                    else:
                        copy.write_row((day, line_no, extra, text, str(path), run_id))
                        loaded += 1
            rejected = len(bad_rows)
            if bad_rows:
                cur.executemany(
                    "INSERT INTO kill_event_rejected "
                    "(dt, line_no, line, error, source_file, run_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    bad_rows)
        res = RunResult(SRC_KILLS, day, read, loaded, rejected)
        if read != loaded + rejected:  # păstrat ca plasă de siguranță: citit = încărcat + respins
            raise RuntimeError(f"Reconciliere eșuată pe {day}: {read} != {loaded} + {rejected}")
        _finish_run(pg, run_id, SRC_KILLS, day, res)
        pg.commit()
    except Exception:
        pg.rollback()
        _record_failure(pg, SRC_KILLS, day)
        raise
    return res
