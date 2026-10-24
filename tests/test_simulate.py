"""Teste pe simulare, fără bază de date (rulează și în CI)."""

import random
from datetime import datetime, timedelta

import pytest

from cod.generator.archetypes import ARCHETYPES, assign_archetypes
from cod.generator.players import build_players
from cod.generator.simulate import ROSTER_SIZE, simulate_matches

BASE_DATE = datetime(2026, 1, 1)
TEAM_A, TEAM_B = 1, 2


def run(seed: int = 42, num_matches: int = 60):
    rng = random.Random(seed)
    ids = list(range(1, 5001))
    return simulate_matches(
        rng,
        all_player_ids=ids,
        archetypes=assign_archetypes(random.Random(seed), ids),
        map_ids=list(range(1, 90)),
        weapon_ids=list(range(1, 66)),
        team_ids=(TEAM_A, TEAM_B),
        num_matches=num_matches,
        pool_size=500,
        base_date=BASE_DATE,
    )


@pytest.fixture(scope="module")
def matches():
    return run()


def team_map(match):
    return {player_id: team_id for player_id, team_id, *_ in match.players}


def test_same_seed_gives_same_result():
    assert run(7) == run(7)


def test_different_seed_gives_different_result():
    assert run(7) != run(8)


def test_players_same_seed_same_result():
    assert build_players(random.Random(1), 100) == build_players(random.Random(1), 100)


def test_gamertags_are_unique():
    tags = [t for t, _ in build_players(random.Random(1), 5000)]
    assert len(tags) == len(set(tags))


def test_each_match_has_12_distinct_players_split_6_6(matches):
    for m in matches:
        assert len(m.players) == ROSTER_SIZE
        assert len({p[0] for p in m.players}) == ROSTER_SIZE
        teams = [p[1] for p in m.players]
        assert teams.count(TEAM_A) == teams.count(TEAM_B) == ROSTER_SIZE // 2


def test_killer_and_victim_are_on_opposite_teams(matches):
    for m in matches:
        team_of = team_map(m)
        for killer, victim, *_ in m.kills:
            assert team_of[killer] != team_of[victim]


def test_assister_is_a_teammate_and_not_the_killer(matches):
    for m in matches:
        team_of = team_map(m)
        for killer, _victim, assister, *_ in m.kills:
            if assister is not None:
                assert assister != killer
                assert team_of[assister] == team_of[killer]


def test_kill_timestamps_are_inside_the_match(matches):
    for m in matches:
        assert all(0 <= k[5] <= m.duration_sec for k in m.kills)


def test_player_totals_equal_the_kill_events(matches):
    for m in matches:
        for player_id, _team, kills, deaths, assists, _score in m.players:
            assert kills == sum(1 for e in m.kills if e[0] == player_id)
            assert deaths == sum(1 for e in m.kills if e[1] == player_id)
            assert assists == sum(1 for e in m.kills if e[2] == player_id)


def test_score_formula(matches):
    for m in matches:
        for _pid, _team, kills, _deaths, assists, score in m.players:
            assert score == kills * 100 + assists * 50


def test_winner_has_the_most_kills(matches):
    for m in matches:
        team_of = team_map(m)
        kills_by_team = {TEAM_A: 0, TEAM_B: 0}
        for killer, *_ in m.kills:
            kills_by_team[team_of[killer]] += 1
        assert kills_by_team[m.winner_team_id] >= max(kills_by_team.values()) - 0
        if kills_by_team[TEAM_A] != kills_by_team[TEAM_B]:
            assert kills_by_team[m.winner_team_id] == max(kills_by_team.values())


def test_started_at_is_in_the_year_before_base_date(matches):
    for m in matches:
        assert BASE_DATE - timedelta(days=366) <= m.started_at <= BASE_DATE


def test_values_fit_the_column_types(matches):
    for m in matches:
        assert m.duration_sec <= 65535
        for _pid, _team, kills, deaths, assists, score in m.players:
            assert max(kills, deaths, assists) <= 127  # tinyint cu semn
            assert score <= 32767


def test_every_assigned_archetype_exists_and_recrut_is_most_common():
    assigned = assign_archetypes(random.Random(3), list(range(1, 3001)))
    assert set(assigned.values()) <= set(ARCHETYPES)
    counts = {a: list(assigned.values()).count(a) for a in ARCHETYPES}
    assert counts["Recrut"] == max(counts.values())
    assert counts["Demon"] < counts["Smoker"]


def test_gamertags_fit_varchar_25():
    assert all(len(t) <= 25 for t, _ in build_players(random.Random(42), 15000))
