"""Linia de comandă a generatorului.

    python -m cod.generator --seed 42 --reset

Pașii (în ordine, cu același `random.Random(seed)` pentru tot): date de referință, jucători,
legături armă-joc, simularea meciurilor. Același seed + aceeași --date dau exact aceleași date.
"""

import argparse
import random
import sys
from datetime import datetime

from cod.db import get_connection
from cod.generator import reference_data as ref
from cod.generator.archetypes import assign_archetypes
from cod.generator.players import build_players
from cod.generator.simulate import simulate_matches

# Ordinea contează: întâi tabelele care depind de celelalte (FK-uri).
TABLES_DELETE_ORDER = [
    "kill_table", "match_player", "`match`", "weapon_game",
    "weapon", "map", "game", "team", "player",
]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Generator de date sintetice COD Scoreboard")
    p.add_argument("--seed", type=int, default=42, help="seed pentru reproductibilitate")
    p.add_argument("--players", type=int, default=15000, help="câți jucători în total")
    p.add_argument("--pool", type=int, default=500, help="câți jucători sunt activi în meciuri")
    p.add_argument("--matches", type=int, default=1500, help="câte meciuri se simulează")
    p.add_argument("--date", default="2026-01-01",
                   help="data de bază (YYYY-MM-DD); meciurile sunt în cele 365 de zile dinainte")
    p.add_argument("--reset", action="store_true",
                   help="GOLEȘTE toate tabelele înainte de inserare")
    p.add_argument("--yes", action="store_true", help="nu mai cere confirmare pentru --reset")
    return p.parse_args(argv)


def _count(cursor, table: str) -> int:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]


def reset_tables(conn, yes: bool) -> None:
    target = f"{conn.server_host}:{conn.server_port}/{conn.database}"
    if not yes:
        answer = input(f"Vei șterge TOATE datele din {target}. Scrie 'da' ca să continui: ")
        if answer.strip().lower() != "da":
            sys.exit("Anulat.")
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in TABLES_DELETE_ORDER:
        cursor.execute(f"TRUNCATE TABLE {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()


def ensure_empty(conn) -> None:
    cursor = conn.cursor()
    filled = [t for t in TABLES_DELETE_ORDER if _count(cursor, t) > 0]
    cursor.close()
    if filled:
        sys.exit(
            "Tabele care nu sunt goale: " + ", ".join(filled)
            + ". Rulează cu --reset ca să le golești, altfel ai datele duplicate."
        )


def seed_reference(conn, rng: random.Random) -> None:
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO game (name, release_year, studio) VALUES (%s, %s, %s)", ref.GAMES)
    cursor.execute("SELECT game_id, name FROM game")
    game_id_of = {name: game_id for game_id, name in cursor.fetchall()}

    maps = [(name, game_id_of[game], size, style) for name, game, size, style in ref.MAPS]
    cursor.executemany(
        "INSERT INTO map (name, game_id, size_category, design_style) VALUES (%s, %s, %s, %s)",
        maps)
    cursor.executemany("INSERT INTO weapon (name, category) VALUES (%s, %s)", ref.WEAPONS)
    cursor.executemany("INSERT INTO team (name) VALUES (%s)", ref.TEAMS)

    # Legături armă-joc: armele iconice apar în 6-10 jocuri, restul în 1-4
    cursor.execute("SELECT weapon_id, name FROM weapon ORDER BY weapon_id")
    weapons = cursor.fetchall()
    cursor.execute("SELECT game_id FROM game ORDER BY game_id")
    game_ids = [r[0] for r in cursor.fetchall()]
    pairs = set()
    for weapon_id, name in weapons:
        links = rng.randint(6, 10) if name in ref.ICONIC_WEAPONS else rng.randint(1, 4)
        for game_id in rng.sample(game_ids, min(len(game_ids), links)):
            pairs.add((weapon_id, game_id))
    cursor.executemany(
        "INSERT INTO weapon_game (weapon_id, game_id) VALUES (%s, %s)", sorted(pairs))
    conn.commit()
    cursor.close()


def seed_players(conn, rng: random.Random, count: int) -> None:
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO player (gamertag, platform, archetype) VALUES (%s, %s, 'Recrut')",
        build_players(rng, count))
    conn.commit()
    cursor.close()


def load_matches(conn, rng: random.Random, args, base_date: datetime) -> tuple[int, int, int]:
    cursor = conn.cursor()

    def ids(sql: str) -> list[int]:
        cursor.execute(sql)
        return [r[0] for r in cursor.fetchall()]

    all_player_ids = ids("SELECT player_id FROM player ORDER BY player_id")
    map_ids = ids("SELECT map_id FROM map ORDER BY map_id")
    weapon_ids = ids("SELECT weapon_id FROM weapon ORDER BY weapon_id")
    team_ids = ids("SELECT team_id FROM team ORDER BY team_id")

    archetypes = assign_archetypes(rng, all_player_ids)
    cursor.executemany(
        "UPDATE player SET archetype = %s WHERE player_id = %s",
        [(a, p) for p, a in archetypes.items()])

    matches = simulate_matches(
        rng,
        all_player_ids=all_player_ids, archetypes=archetypes,
        map_ids=map_ids, weapon_ids=weapon_ids,
        team_ids=(team_ids[0], team_ids[1]),
        num_matches=args.matches, pool_size=args.pool, base_date=base_date,
    )

    kill_rows, mp_rows = [], []
    for m in matches:
        cursor.execute(
            "INSERT INTO `match` (map_id, mode, started_at, duration_sec, winner_team_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (m.map_id, m.mode, m.started_at, m.duration_sec, m.winner_team_id))
        match_id = cursor.lastrowid
        kill_rows += [(match_id, *k) for k in m.kills]
        mp_rows += [(match_id, *p) for p in m.players]

    cursor.executemany(
        "INSERT INTO kill_table (match_id, killer_id, victim_id, assister_id, weapon_id, "
        "is_headshot, timestamp_in_match) VALUES (%s, %s, %s, %s, %s, %s, %s)", kill_rows)
    cursor.executemany(
        "INSERT INTO match_player (match_id, player_id, team_id, kills, deaths, assists, score) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)", mp_rows)
    conn.commit()
    cursor.close()
    return len(matches), len(kill_rows), len(mp_rows)


def main(argv=None) -> None:
    args = parse_args(argv)
    base_date = datetime.strptime(args.date, "%Y-%m-%d")
    rng = random.Random(args.seed)

    conn = get_connection()
    try:
        if args.reset:
            reset_tables(conn, args.yes)
        else:
            ensure_empty(conn)
        seed_reference(conn, rng)
        seed_players(conn, rng, args.players)
        n_matches, n_kills, n_mp = load_matches(conn, rng, args, base_date)
    finally:
        conn.close()

    print(f"seed={args.seed}: {args.players} jucători, {n_matches} meciuri, "
          f"{n_kills} kill-uri, {n_mp} rânduri match_player.")
