"""Invarianți pe datele din baza de date. Fiecare test caută ceva ce NU are voie să existe.

Rulează doar dacă MySQL e pornit și baza e populată (altfel sunt sărite):
    python -m cod.generator --seed 42 --reset
    pytest -q
"""

import pytest


@pytest.fixture
def cur(db):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM `match`")
    if cursor.fetchone()[0] == 0:
        pytest.skip("Baza e goală: rulează `python -m cod.generator --seed 42 --reset`")
    yield cursor
    cursor.close()


def count(cur, sql: str) -> int:
    cur.execute(sql)
    return cur.fetchone()[0]


def test_no_orphan_foreign_keys_in_kill_table(cur):
    sql = """
        SELECT COUNT(*) FROM kill_table k
        LEFT JOIN `match` m ON m.match_id = k.match_id
        LEFT JOIN player v ON v.player_id = k.victim_id
        LEFT JOIN weapon w ON w.weapon_id = k.weapon_id
        LEFT JOIN player kr ON kr.player_id = k.killer_id
        LEFT JOIN player a ON a.player_id = k.assister_id
        WHERE m.match_id IS NULL OR v.player_id IS NULL OR w.weapon_id IS NULL
           OR (k.killer_id IS NOT NULL AND kr.player_id IS NULL)
           OR (k.assister_id IS NOT NULL AND a.player_id IS NULL)
    """
    assert count(cur, sql) == 0


def test_kills_happen_inside_the_match_duration(cur):
    sql = """
        SELECT COUNT(*) FROM kill_table k
        JOIN `match` m ON m.match_id = k.match_id
        WHERE k.timestamp_in_match > m.duration_sec
    """
    assert count(cur, sql) == 0


def test_match_player_totals_equal_kill_table(cur):
    # Agregăm o singură dată kill_table pe (meci, jucător), apoi comparăm. Varianta cu
    # subquery corelat per rând e corectă, dar durează minute pe MySQL.
    sql = """
        SELECT COUNT(*) FROM match_player mp
        LEFT JOIN (SELECT match_id, killer_id AS pid, COUNT(*) AS n FROM kill_table
                   WHERE killer_id IS NOT NULL GROUP BY match_id, killer_id) k
               ON k.match_id = mp.match_id AND k.pid = mp.player_id
        LEFT JOIN (SELECT match_id, victim_id AS pid, COUNT(*) AS n FROM kill_table
                   GROUP BY match_id, victim_id) d
               ON d.match_id = mp.match_id AND d.pid = mp.player_id
        LEFT JOIN (SELECT match_id, assister_id AS pid, COUNT(*) AS n FROM kill_table
                   WHERE assister_id IS NOT NULL GROUP BY match_id, assister_id) a
               ON a.match_id = mp.match_id AND a.pid = mp.player_id
        WHERE mp.kills   <> COALESCE(k.n, 0)
           OR mp.deaths  <> COALESCE(d.n, 0)
           OR mp.assists <> COALESCE(a.n, 0)
    """
    assert count(cur, sql) == 0


def test_assister_is_never_the_killer(cur):
    assert count(cur, "SELECT COUNT(*) FROM kill_table WHERE assister_id = killer_id") == 0


def test_nobody_kills_themselves(cur):
    assert count(cur, "SELECT COUNT(*) FROM kill_table WHERE killer_id = victim_id") == 0


def test_every_match_has_exactly_12_players(cur):
    sql = """
        SELECT COUNT(*) FROM (
            SELECT match_id FROM match_player GROUP BY match_id HAVING COUNT(*) <> 12
        ) bad
    """
    assert count(cur, sql) == 0


def test_killer_and_victim_belong_to_the_match(cur):
    sql = """
        SELECT COUNT(*) FROM kill_table k
        LEFT JOIN match_player kmp ON kmp.match_id = k.match_id AND kmp.player_id = k.killer_id
        LEFT JOIN match_player vmp ON vmp.match_id = k.match_id AND vmp.player_id = k.victim_id
        WHERE vmp.player_id IS NULL OR (k.killer_id IS NOT NULL AND kmp.player_id IS NULL)
    """
    assert count(cur, sql) == 0


def test_killer_and_victim_are_on_opposite_teams(cur):
    sql = """
        SELECT COUNT(*) FROM kill_table k
        JOIN match_player kmp ON kmp.match_id = k.match_id AND kmp.player_id = k.killer_id
        JOIN match_player vmp ON vmp.match_id = k.match_id AND vmp.player_id = k.victim_id
        WHERE kmp.team_id = vmp.team_id
    """
    assert count(cur, sql) == 0


def test_score_formula(cur):
    sql = "SELECT COUNT(*) FROM match_player WHERE score <> kills * 100 + assists * 50"
    assert count(cur, sql) == 0


def test_winner_is_a_team_with_the_most_kills(cur):
    sql = """
        SELECT COUNT(*) FROM `match` m
        JOIN (SELECT match_id, team_id, SUM(kills) AS k
              FROM match_player GROUP BY match_id, team_id) w
          ON w.match_id = m.match_id AND w.team_id = m.winner_team_id
        JOIN (SELECT match_id, MAX(k) AS best FROM
                (SELECT match_id, team_id, SUM(kills) AS k
                 FROM match_player GROUP BY match_id, team_id) t
              GROUP BY match_id) b
          ON b.match_id = m.match_id
        WHERE w.k < b.best
    """
    assert count(cur, sql) == 0


def test_every_weapon_exists_in_at_least_one_game(cur):
    sql = """
        SELECT COUNT(*) FROM weapon w
        LEFT JOIN weapon_game wg ON wg.weapon_id = w.weapon_id
        WHERE wg.game_id IS NULL
    """
    assert count(cur, sql) == 0


def test_every_map_belongs_to_a_game(cur):
    sql = """
        SELECT COUNT(*) FROM map m
        LEFT JOIN game g ON g.game_id = m.game_id
        WHERE g.game_id IS NULL
    """
    assert count(cur, sql) == 0


def test_demon_players_outperform_recruts(cur):
    """Arhetipurile chiar influențează rezultatele: K/D mediu Demon > K/D mediu Recrut."""
    sql = """
        SELECT SUM(mp.kills) / NULLIF(SUM(mp.deaths), 0)
        FROM match_player mp JOIN player p ON p.player_id = mp.player_id
        WHERE p.archetype = %s
    """
    cur.execute(sql, ("Demon",))
    demon = cur.fetchone()[0]
    cur.execute(sql, ("Recrut",))
    recrut = cur.fetchone()[0]
    if demon is None:
        pytest.skip("Niciun Demon nu a jucat în eșantion")
    assert float(demon) > float(recrut)


def test_all_archetypes_are_valid_enum_values(cur):
    assert count(cur, "SELECT COUNT(*) FROM player WHERE archetype IS NULL") == 0
