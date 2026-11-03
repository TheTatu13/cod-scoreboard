"""Teste pentru views și query-urile analitice (Faza 2).

Principiu: o view nu are voie să dea alte numere decât tabelele din care e făcută. Comparăm
fiecare view cu un calcul independent, direct pe tabelele de bază.

Rulează doar dacă MySQL e pornit și baza e populată (altfel sunt sărite).
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VIEWS_FILE = ROOT / "sql" / "schema" / "02_views.sql"
QUERY_FILES = sorted(p for p in (ROOT / "sql" / "queries").glob("0*.sql"))


def _statements(sql_text: str):
    """Împarte un fișier .sql în instrucțiuni (scoate comentariile `--`)."""
    lines = [ln for ln in sql_text.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


@pytest.fixture
def cur(db):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM `match`")
    if cursor.fetchone()[0] == 0:
        pytest.skip("Baza e goală: rulează `python -m cod.generator --seed 42 --reset`")
    for statement in _statements(VIEWS_FILE.read_text(encoding="utf-8")):
        cursor.execute(statement)
    yield cursor
    cursor.close()


def one(cur, sql: str):
    cur.execute(sql)
    return cur.fetchone()[0]


def test_player_stats_has_one_row_per_active_player(cur):
    assert one(cur, "SELECT COUNT(*) FROM v_player_stats") == one(
        cur, "SELECT COUNT(DISTINCT player_id) FROM match_player")


def test_player_stats_kills_match_the_base_table(cur):
    assert one(cur, "SELECT SUM(total_kills) FROM v_player_stats") == one(
        cur, "SELECT SUM(kills) FROM match_player")


def test_kd_ratio_is_kills_over_deaths(cur):
    sql = """
        SELECT COUNT(*) FROM v_player_stats
        WHERE total_deaths > 0 AND ABS(kd_ratio - total_kills / total_deaths) > 0.01
    """
    assert one(cur, sql) == 0


def test_weapon_stats_cover_every_kill_with_a_weapon(cur):
    assert one(cur, "SELECT SUM(total_kills) FROM v_weapon_stats") == one(
        cur, "SELECT COUNT(*) FROM kill_table WHERE weapon_id IS NOT NULL")


def test_headshots_never_exceed_kills_and_pct_is_valid(cur):
    sql = """
        SELECT COUNT(*) FROM v_weapon_stats
        WHERE headshots > total_kills OR headshot_pct < 0 OR headshot_pct > 100
    """
    assert one(cur, sql) == 0


def test_headshot_pct_is_headshots_over_kills(cur):
    sql = """
        SELECT COUNT(*) FROM v_weapon_stats
        WHERE total_kills > 0 AND ABS(headshot_pct - 100 * headshots / total_kills) > 0.1
    """
    assert one(cur, sql) == 0


def test_map_stats_count_each_kill_exactly_once(cur):
    # Dacă JOIN-urile ar înmulți rânduri, suma ar depăși numărul real de kill-uri.
    assert one(cur, "SELECT SUM(total_kills) FROM v_map_stats") == one(
        cur, "SELECT COUNT(*) FROM kill_table k JOIN `match` m ON m.match_id = k.match_id "
             "WHERE m.map_id IS NOT NULL")


def test_map_stats_matches_equal_total_matches(cur):
    assert one(cur, "SELECT SUM(matches_played) FROM v_map_stats") == one(
        cur, "SELECT COUNT(*) FROM `match` WHERE map_id IS NOT NULL")


def test_archetype_stats_add_up_to_player_stats(cur):
    assert one(cur, "SELECT SUM(players) FROM v_archetype_stats") == one(
        cur, "SELECT COUNT(*) FROM v_player_stats")
    assert one(cur, "SELECT SUM(total_kills) FROM v_archetype_stats") == one(
        cur, "SELECT SUM(total_kills) FROM v_player_stats")


@pytest.mark.parametrize("path", QUERY_FILES, ids=lambda p: p.name)
def test_every_analytical_query_runs(cur, path):
    statements = _statements(path.read_text(encoding="utf-8"))
    assert len(statements) == 1, "un fișier = o interogare"
    cur.execute(statements[0])
    cur.fetchall()  # dacă SQL-ul are o eroare, execute() ridică excepție


def test_inactive_players_query_agrees_with_stats_view(cur):
    registered = one(cur, "SELECT COUNT(*) FROM player")
    active = one(cur, "SELECT COUNT(*) FROM v_player_stats")
    cur.execute(_statements((ROOT / "sql" / "queries" / "05_inactive_players.sql")
                            .read_text(encoding="utf-8"))[0])
    total, never_played, _pct = cur.fetchone()
    assert total == registered
    assert never_played == registered - active
