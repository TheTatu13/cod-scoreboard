"""Teste pentru ingestie (Faza 3): idempotență, watermark, atomicitate, reconciliere cu manifestul.

Au nevoie de MySQL populat și de PostgreSQL pornit; altfel sunt sărite. Fiecare test lucrează
într-o schemă PostgreSQL temporară, nu în `raw`.
"""

import shutil
from datetime import date

import pytest

from cod.db import get_connection
from cod.ingest import loaders
from cod.ingest.cli import main


def scalar(pg, sql: str, params=()):
    with pg.conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def mysql_scalar(sql: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchone()[0]
    finally:
        conn.close()


def run(pg, events_dir, *extra):
    return main(["--events-dir", str(events_dir), "--schema", pg.schema, *extra])


# ---------- idempotență ----------

def test_loading_the_same_day_twice_changes_nothing(pg, feed):
    events_dir, _ = feed
    day = loaders.partition_days(events_dir)[100]
    my = get_connection()
    try:
        loaders.load_reference(my, pg.conn)
        counts = []
        for _ in range(2):
            loaders.load_matches(my, pg.conn, day)
            loaders.load_kills(pg.conn, events_dir, day)
            counts.append(tuple(scalar(pg, f"SELECT COUNT(*) FROM {t}")
                                for t in ("match", "match_player", "kill_event")))
    finally:
        my.close()
    assert counts[0] == counts[1]
    assert counts[0][2] > 0  # ziua aleasă are într-adevăr kill-uri


def test_running_the_whole_pipeline_twice_gives_identical_tables(pg, feed):
    events_dir, _ = feed
    run(pg, events_dir)
    first = {t: scalar(pg, f"SELECT COUNT(*) FROM {t}")
             for t in ("player", "match", "match_player", "kill_event")}
    # a doua rulare pe TOT intervalul (nu doar incremental): trebuie să dea aceleași numere
    run(pg, events_dir, "--from", "2000-01-01", "--to", "2030-12-31")
    second = {t: scalar(pg, f"SELECT COUNT(*) FROM {t}") for t in first}
    assert first == second


# ---------- reconciliere cu manifestul (adevărul din generator) ----------

@pytest.fixture
def loaded(pg, feed):
    events_dir, manifest = feed
    run(pg, events_dir)
    return pg, manifest


def test_every_emitted_row_is_in_raw(loaded):
    pg, manifest = loaded
    assert scalar(pg, "SELECT COUNT(*) FROM kill_event") == manifest["emitted_rows"]
    assert scalar(pg, "SELECT COUNT(*) FROM kill_event_rejected") == 0
    assert scalar(pg, "SELECT COUNT(DISTINCT event_id) FROM kill_event") == manifest["clean_events"]


def test_raw_keeps_duplicates_untouched(loaded):
    pg, manifest = loaded
    extra = scalar(pg, "SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM kill_event")
    assert extra == manifest["counts"]["duplicate"]


def test_raw_keeps_late_events_in_their_delivery_partition(loaded):
    pg, manifest = loaded
    late_ids = manifest["defects"]["late"]
    out_of_day = scalar(pg, "SELECT COUNT(*) FROM kill_event "
                            "WHERE (payload->>'event_time')::date <> dt")
    rows_of_late_ids = scalar(pg, "SELECT COUNT(*) FROM kill_event WHERE event_id = ANY(%s)",
                              (late_ids,))
    assert out_of_day == rows_of_late_ids


def test_raw_keeps_schema_drift_as_is(loaded):
    pg, manifest = loaded
    drift = manifest["schema_drift"]["rows"]
    assert scalar(pg, "SELECT COUNT(*) FROM kill_event WHERE payload ? 'headshot'") == drift
    assert scalar(pg, "SELECT COUNT(*) FROM kill_event WHERE payload ? 'is_headshot'") == (
        manifest["emitted_rows"] - drift)


def test_raw_does_not_clean_orphan_victims(loaded):
    """Stratul raw nu corectează nimic: victimele inexistente trebuie să fie încă acolo."""
    pg, manifest = loaded
    orphans = scalar(pg, """
        SELECT COUNT(DISTINCT event_id) FROM kill_event
        WHERE (payload->>'victim_id') IS NOT NULL
          AND (payload->>'victim_id')::int NOT IN (SELECT player_id FROM player)
    """)
    assert orphans == manifest["counts"]["orphan_victim"]


def test_raw_tables_match_mysql_row_counts(loaded):
    pg, _ = loaded
    for table in ("player", "match", "match_player", "weapon", "map", "game", "team"):
        mysql_name = "`match`" if table == "match" else table
        assert scalar(pg, f"SELECT COUNT(*) FROM {table}") == mysql_scalar(
            f"SELECT COUNT(*) FROM {mysql_name}"), table


# ---------- incremental și watermark ----------

def test_incremental_run_after_full_load_is_a_noop(loaded, feed):
    pg, _ = loaded
    events_dir, _ = feed
    assert run(pg, events_dir) == []
    last = max(loaders.partition_days(events_dir))
    assert loaders.get_watermark(pg.conn, loaders.SRC_KILLS) == last


def test_incremental_picks_up_only_the_new_partition(pg, feed, tmp_path):
    events_dir, _ = feed
    days = loaders.partition_days(events_dir)
    small = tmp_path / "events"
    for d in days[:3]:
        shutil.copytree(events_dir / f"dt={d}", small / f"dt={d}")
    run(pg, small)
    assert loaders.get_watermark(pg.conn, loaders.SRC_KILLS) == days[2]

    shutil.copytree(events_dir / f"dt={days[3]}", small / f"dt={days[3]}")
    results = run(pg, small)
    kill_runs = [r for r in results if r.source == loaders.SRC_KILLS]
    assert [r.day for r in kill_runs] == [days[3]]
    assert scalar(pg, "SELECT COUNT(DISTINCT dt) FROM kill_event") == 4


def test_watermark_never_moves_backwards(pg, feed):
    events_dir, _ = feed
    days = loaders.partition_days(events_dir)
    run(pg, events_dir, "--day", days[50].isoformat())
    run(pg, events_dir, "--day", days[10].isoformat())
    assert loaders.get_watermark(pg.conn, loaders.SRC_KILLS) == days[50]


# ---------- linii invalide și atomicitate ----------

def test_invalid_lines_are_quarantined_and_counted(pg, tmp_path):
    day = date(2025, 3, 5)
    part = tmp_path / f"dt={day}"
    part.mkdir()
    (part / "kills.jsonl").write_text(
        '{"event_id": "k1", "victim_id": 5}\n'
        'asta nu e json\n'
        '\n'
        '[1, 2, 3]\n'
        '{"event_id": "k2", "victim_id": 6}\n', encoding="utf-8")
    for _ in range(2):  # și a doua oară, ca să verificăm idempotența
        res = loaders.load_kills(pg.conn, tmp_path, day)
        assert (res.rows_read, res.rows_loaded, res.rows_rejected) == (4, 2, 2)
        assert scalar(pg, "SELECT COUNT(*) FROM kill_event") == 2
        assert scalar(pg, "SELECT COUNT(*) FROM kill_event_rejected") == 2


def test_failed_day_is_rolled_back_and_recorded(pg, feed, monkeypatch):
    events_dir, _ = feed
    day = loaders.partition_days(events_dir)[5]

    def boom(*args, **kwargs):
        raise RuntimeError("cădere simulată")

    monkeypatch.setattr(loaders, "_finish_run", boom)
    with pytest.raises(RuntimeError):
        loaders.load_kills(pg.conn, events_dir, day)
    assert scalar(pg, "SELECT COUNT(*) FROM kill_event") == 0  # nimic pe jumătate
    assert scalar(pg, "SELECT COUNT(*) FROM ingest_run WHERE status = 'failed'") == 1
    assert loaders.get_watermark(pg.conn, loaders.SRC_KILLS) is None


def test_ingest_run_log_matches_what_was_loaded(loaded):
    pg, manifest = loaded
    read = scalar(pg, "SELECT SUM(rows_read) FROM ingest_run "
                      "WHERE source = 'feed.kills' AND status = 'ok'")
    written = scalar(pg, "SELECT SUM(rows_loaded + rows_rejected) FROM ingest_run "
                         "WHERE source = 'feed.kills' AND status = 'ok'")
    assert read == written == manifest["emitted_rows"]
