"""Linia de comandă a ingestiei.

    python -m cod.ingest                      # incremental: doar zilele după watermark
    python -m cod.ingest --day 2025-03-05     # o zi anume (idempotent, poți s-o repeți)
    python -m cod.ingest --from 2025-01-01 --to 2025-01-31   # backfill pe un interval

Pași: (1) creează tabelele raw dacă lipsesc, (2) copiază tabelele de referință din MySQL,
(3) pentru fiecare zi, încarcă meciurile din MySQL și partiția JSON de kill-uri.
"""

import argparse
from datetime import date, timedelta
from pathlib import Path

from cod.db import get_connection, get_pg_connection
from cod.ingest import loaders


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Ingestie MySQL + JSON -> PostgreSQL raw")
    p.add_argument("--events-dir", default="data/events", help="folderul feed-ului JSON")
    p.add_argument("--schema", default="raw", help="schema PostgreSQL țintă")
    when = p.add_mutually_exclusive_group()
    when.add_argument("--day", type=date.fromisoformat, help="o singură zi (YYYY-MM-DD)")
    when.add_argument("--from", dest="start", type=date.fromisoformat,
                      help="începutul intervalului; cere și --to")
    p.add_argument("--to", dest="end", type=date.fromisoformat, help="sfârșitul intervalului")
    return p.parse_args(argv)


def match_days(my) -> list[date]:
    cursor = my.cursor()
    cursor.execute("SELECT DISTINCT DATE(started_at) FROM `match` ORDER BY 1")
    days = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return days


def plan_days(args, my, pg, events_dir: Path) -> tuple[list[date], set[date], set[date]]:
    """Returnează (zile de procesat, zile cu feed, zile cu meciuri)."""
    feed = set(loaders.partition_days(events_dir))
    matches = set(match_days(my))
    if args.day:
        return [args.day], feed & {args.day}, matches & {args.day}
    if args.start:
        if not args.end:
            raise SystemExit("--from cere și --to")
        span = {args.start + timedelta(days=i) for i in range((args.end - args.start).days + 1)}
        feed, matches = feed & span, matches & span
    else:  # incremental: doar zilele de după watermark-ul fiecărei surse
        wm_feed = loaders.get_watermark(pg, loaders.SRC_KILLS)
        wm_match = loaders.get_watermark(pg, loaders.SRC_MATCH)
        feed = {d for d in feed if wm_feed is None or d > wm_feed}
        matches = {d for d in matches if wm_match is None or d > wm_match}
    return sorted(feed | matches), feed, matches


def main(argv=None) -> list[loaders.RunResult]:
    args = parse_args(argv)
    events_dir = Path(args.events_dir)
    my = get_connection()
    pg = get_pg_connection(args.schema)
    results: list[loaders.RunResult] = []
    try:
        loaders.ensure_schema(pg)
        ref = loaders.load_reference(my, pg)
        days, feed_days, match_set = plan_days(args, my, pg, events_dir)
        for day in days:
            if day in match_set:
                r = loaders.load_matches(my, pg, day)
                if r:
                    results.append(r)
            if day in feed_days:
                r = loaders.load_kills(pg, events_dir, day)
                if r:
                    results.append(r)
    finally:
        my.close()
        pg.close()
    kills = [r for r in results if r.source == loaders.SRC_KILLS]
    matches = [r for r in results if r.source == loaders.SRC_MATCH]
    print(f"referință: {sum(ref.values())} rânduri în {len(ref)} tabele")
    print(f"meciuri: {len(matches)} zile, {sum(r.rows_loaded for r in matches)} rânduri")
    print(f"kill-uri: {len(kills)} zile, citite {sum(r.rows_read for r in kills)}, "
          f"încărcate {sum(r.rows_loaded for r in kills)}, "
          f"respinse {sum(r.rows_rejected for r in kills)}")
    if not results:
        print("nimic nou de încărcat")
    return results


if __name__ == "__main__":
    main()
