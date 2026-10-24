"""Exportă kill-urile din MySQL ca feed JSON (sursa murdară pentru pipeline).

    python -m cod.generator.events --seed 42 --out data/events

Scrie `data/events/dt=YYYY-MM-DD/kills.jsonl` (un eveniment pe linie, partiționat pe ZIUA DE
LIVRARE) și `data/events/_manifest.json` (adevărul: ce defecte au fost injectate). Cu `--clean`
nu injectează nimic. Folderul de ieșire e golit la fiecare rulare, deci e idempotent.
"""

import argparse
import json
import random
import shutil
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from cod.db import get_connection
from cod.generator.chaos import ChaosConfig, inject_chaos

SQL = """
    SELECT k.kill_id, k.match_id, m.started_at, m.duration_sec, k.killer_id, k.victim_id,
           k.assister_id, w.name, k.is_headshot, k.timestamp_in_match
    FROM kill_table k
    JOIN `match` m ON m.match_id = k.match_id
    JOIN weapon w ON w.weapon_id = k.weapon_id
    ORDER BY k.kill_id
"""


def fetch_events(conn) -> tuple[list[dict], int]:
    cursor = conn.cursor()
    cursor.execute(SQL)
    events = []
    for (kill_id, match_id, started_at, duration, killer, victim, assister, weapon,
         headshot, ts) in cursor.fetchall():
        event_time = started_at + timedelta(seconds=ts)
        events.append({
            "event_id": f"k{kill_id}",
            "match_id": match_id,
            "event_time": event_time.isoformat(),
            "killer_id": killer,
            "victim_id": victim,
            "assister_id": assister,
            "weapon": weapon,
            "is_headshot": bool(headshot),
            "timestamp_in_match": ts,
            "match_duration_sec": duration,
        })
    cursor.execute("SELECT MAX(player_id) FROM player")
    max_player_id = cursor.fetchone()[0]
    cursor.close()
    return events, max_player_id


def write_partitions(rows: list[tuple[date, dict]], out_dir: Path) -> int:
    """Scrie rândurile în dt=<zi>/kills.jsonl. Golește `out_dir` înainte (idempotent)."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    by_day = defaultdict(list)
    for day, row in rows:
        by_day[day].append(row)
    for day, day_rows in sorted(by_day.items()):
        part = out_dir / f"dt={day.isoformat()}"
        part.mkdir(parents=True)
        with open(part / "kills.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for row in day_rows:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    out_dir.mkdir(parents=True, exist_ok=True)
    return len(by_day)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Exportă kill-urile ca feed JSON, cu defecte")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="data/events")
    p.add_argument("--clean", action="store_true", help="fără defecte injectate")
    args = p.parse_args(argv)

    conn = get_connection()
    try:
        events, max_player_id = fetch_events(conn)
    finally:
        conn.close()
    if not events:
        raise SystemExit("kill_table e goală. Rulează întâi `python -m cod.generator --reset`.")

    cfg = ChaosConfig(**({k: 0.0 for k in (
        "orphan_victim", "self_kill", "ts_out_of_range", "dirty_weapon",
        "missing_field", "duplicate", "late")} if args.clean else {}))
    rows, manifest = inject_chaos(
        random.Random(args.seed), events, cfg, max_player_id=max_player_id)
    manifest["seed"] = args.seed

    out_dir = Path(args.out)
    n_days = write_partitions(rows, out_dir)
    (out_dir / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(events)} evenimente curate -> {len(rows)} rânduri în {n_days} zile. "
          f"Defecte: {manifest['counts']}")


if __name__ == "__main__":
    main()
