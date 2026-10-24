"""Simularea meciurilor, fără bază de date.

Logica vine din simulate_matches.py. Funcția `simulate_matches` e pură: primește ID-urile
existente și un `random.Random` cu seed, și returnează rândurile care se vor insera. Așa poate
fi testată fără MySQL, iar același seed produce exact același rezultat.

Invarianți garantați prin construcție:
- killer și victim sunt în echipe opuse;
- assister e din echipa killer-ului și nu e killer-ul;
- timestamp_in_match e între 0 și duration_sec;
- match_player.kills/deaths/assists vin din aceleași evenimente ca kill_table;
- câștigătorul e echipa cu mai multe kill-uri (la egalitate se alege la întâmplare).
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from cod.generator.archetypes import roll_abilities

MODES = ["Team Deathmatch", "Domination", "Kill Confirmed", "Hardpoint"]
ROSTER_SIZE = 12
KILLS_PER_MATCH = (40, 80)
DURATION_SEC = (300, 900)
ASSIST_CHANCE = 0.3
HEADSHOT_CHANCE = 0.2
DAYS_BACK = 365


@dataclass
class SimulatedMatch:
    map_id: int
    mode: str
    started_at: datetime
    duration_sec: int
    winner_team_id: int
    # (killer, victim, assister, weapon_id, is_headshot, timestamp_in_match)
    kills: list[tuple] = field(default_factory=list)
    # (player_id, team_id, kills, deaths, assists, score)
    players: list[tuple] = field(default_factory=list)


def simulate_matches(
    rng: random.Random,
    *,
    all_player_ids: list[int],
    archetypes: dict[int, str],
    map_ids: list[int],
    weapon_ids: list[int],
    team_ids: tuple[int, int],
    num_matches: int,
    pool_size: int,
    base_date: datetime,
) -> list[SimulatedMatch]:
    team_a_id, team_b_id = team_ids

    # Pool activ + abilități ascunse (skill = cât de bun e, support = cât ajută)
    pool = rng.sample(all_player_ids, pool_size)
    skill, support = {}, {}
    for p in pool:
        skill[p], support[p] = roll_abilities(rng, archetypes[p])

    matches = []
    for _ in range(num_matches):
        participants = rng.sample(pool, ROSTER_SIZE)
        half = ROSTER_SIZE // 2
        team_a, team_b = participants[:half], participants[half:]
        team_of = {p: team_a_id for p in team_a}
        team_of.update({p: team_b_id for p in team_b})

        duration = rng.randint(*DURATION_SEC)

        events = []
        for _ in range(rng.randint(*KILLS_PER_MATCH)):
            killer = rng.choices(participants, weights=[skill[p] for p in participants])[0]
            enemies = team_b if killer in team_a else team_a
            victim = rng.choices(enemies, weights=[1 / skill[p] for p in enemies])[0]

            assister = None
            if rng.random() < ASSIST_CHANCE:
                mates = [p for p in (team_a if killer in team_a else team_b) if p != killer]
                assister = rng.choices(mates, weights=[support[p] for p in mates])[0]

            events.append((
                killer, victim, assister, rng.choice(weapon_ids),
                rng.random() < HEADSHOT_CHANCE, rng.randint(0, duration),
            ))

        kills_a = sum(1 for e in events if e[0] in team_a)
        kills_b = len(events) - kills_a
        if kills_a == kills_b:
            winner = rng.choice([team_a_id, team_b_id])
        else:
            winner = team_a_id if kills_a > kills_b else team_b_id

        started_at = base_date - timedelta(
            days=rng.randint(0, DAYS_BACK),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )

        match = SimulatedMatch(
            map_id=rng.choice(map_ids),
            mode=rng.choice(MODES),
            started_at=started_at,
            duration_sec=duration,
            winner_team_id=winner,
            kills=events,
        )
        for p in participants:
            k = sum(1 for e in events if e[0] == p)
            d = sum(1 for e in events if e[1] == p)
            a = sum(1 for e in events if e[2] == p)
            match.players.append((p, team_of[p], k, d, a, k * 100 + a * 50))
        matches.append(match)

    return matches
