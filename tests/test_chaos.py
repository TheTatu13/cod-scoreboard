"""Teste pe injectarea de defecte, fără bază de date."""

import json
import random
from datetime import date

from cod.generator.chaos import DEFECTS, ChaosConfig, inject_chaos
from cod.generator.events import write_partitions

MAX_PLAYER = 1000


def make_events(n: int = 5000):
    events = []
    for i in range(1, n + 1):
        day = 1 + (i % 28)
        events.append({
            "event_id": f"k{i}",
            "match_id": i // 60 + 1,
            "event_time": f"2025-06-{day:02d}T12:{i % 60:02d}:00",
            "killer_id": 1 + i % 500,
            "victim_id": 501 + i % 500,
            "assister_id": None,
            "weapon": "M4A1",
            "is_headshot": bool(i % 5 == 0),
            "timestamp_in_match": 100 + i % 300,
            "match_duration_sec": 600,
        })
    return events


def run(seed=1, cfg=None):
    return inject_chaos(
        random.Random(seed), make_events(), cfg or ChaosConfig(), max_player_id=MAX_PLAYER)


def test_same_seed_same_chaos():
    assert run(1) == run(1)


def test_different_seed_different_chaos():
    assert run(1)[1]["defects"] != run(2)[1]["defects"]


def test_zero_rates_change_nothing():
    zero = ChaosConfig(0, 0, 0, 0, 0, 0, 0)
    rows, manifest = run(1, zero)
    assert manifest["counts"] == dict.fromkeys(DEFECTS, 0)
    assert len(rows) == 5000


def test_row_count_is_clean_plus_duplicates():
    rows, manifest = run()
    assert manifest["emitted_rows"] == len(rows)
    assert len(rows) == manifest["clean_events"] + manifest["counts"]["duplicate"]


def test_every_defect_type_appears():
    _, manifest = run()
    assert all(manifest["counts"][d] > 0 for d in DEFECTS)


def test_rates_are_close_to_configured():
    _, manifest = run()
    assert 0.01 < manifest["counts"]["duplicate"] / 5000 < 0.035
    assert 0.015 < manifest["counts"]["late"] / 5000 < 0.05


def by_id(rows):
    out = {}
    for _day, row in rows:
        out.setdefault(row["event_id"], row)
    return out


def test_manifest_matches_what_is_actually_broken():
    rows, manifest = run()
    rows_by_id = by_id(rows)
    for eid in manifest["defects"]["orphan_victim"]:
        assert rows_by_id[eid]["victim_id"] > MAX_PLAYER
    for eid in manifest["defects"]["self_kill"]:
        assert rows_by_id[eid]["killer_id"] == rows_by_id[eid]["victim_id"]
    for eid in manifest["defects"]["ts_out_of_range"]:
        r = rows_by_id[eid]
        assert r["timestamp_in_match"] < 0 or r["timestamp_in_match"] > r["match_duration_sec"]
    for eid in manifest["defects"]["dirty_weapon"]:
        assert rows_by_id[eid]["weapon"] != "M4A1"
    for eid in manifest["defects"]["missing_field"]:
        r = rows_by_id[eid]
        assert r["victim_id"] is None or r["weapon"] is None


def test_exclusive_defects_do_not_overlap():
    _, manifest = run()
    names = ("orphan_victim", "self_kill", "ts_out_of_range", "dirty_weapon", "missing_field")
    seen = set()
    for n in names:
        ids = set(manifest["defects"][n])
        assert not (seen & ids)
        seen |= ids


def test_duplicates_are_really_two_rows():
    rows, manifest = run()
    counts = {}
    for _day, row in rows:
        counts[row["event_id"]] = counts.get(row["event_id"], 0) + 1
    assert {e for e, c in counts.items() if c == 2} == set(manifest["defects"]["duplicate"])


def test_late_events_arrive_after_they_happened():
    rows, manifest = run()
    late = set(manifest["defects"]["late"])
    for day, row in rows:
        happened = date.fromisoformat(row["event_time"][:10])
        if row["event_id"] in late:
            assert day > happened
        else:
            assert day == happened


def test_schema_drift_only_in_late_partitions():
    rows, manifest = run()
    start = manifest["schema_drift"]["from"]
    assert manifest["schema_drift"]["rows"] > 0
    for day, row in rows:
        if day.isoformat() >= start:
            assert "headshot" in row and "is_headshot" not in row
            assert row["client_version"] == "2.1"
        else:
            assert "is_headshot" in row and "headshot" not in row


def test_write_partitions_is_idempotent_and_partitioned(tmp_path):
    rows, _ = run()
    out = tmp_path / "events"
    n1 = write_partitions(rows, out)
    first = sorted(p.name for p in out.iterdir())
    (out / "junk.txt").write_text("rămășiță dintr-o rulare veche", encoding="utf-8")
    n2 = write_partitions(rows, out)
    assert n1 == n2
    assert sorted(p.name for p in out.iterdir()) == first
    lines = (out / first[0] / "kills.jsonl").read_text(encoding="utf-8").splitlines()
    assert all(json.loads(line)["event_id"].startswith("k") for line in lines)
