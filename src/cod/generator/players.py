"""Generarea jucătorilor (gamertag + platformă). Logica din seed_player.py, cu rng cu seed."""

import random

CHARACTER_NAMES = [
    "Masked", "Ghost", "Price", "Soap", "Makarov", "Woods", "Reznov",
    "Menendez", "Roach", "Yuri", "Farah", "Gaz", "Alex", "Bale", "Nikolai",
    "Sandman", "Truck", "Grinch", "Frost", "Ghillie", "Merrick", "Keegan",
    "Hesh", "Logan", "Elias", "Rorke", "Salazar", "Cormack", "Chaos",
    "Ajax", "Ruin", "Prophet", "Reyes", "Kane", "Hendricks", "Vonderhaar",
    "Adler", "Bell", "Park", "Lazar", "Weaver", "Graves", "Konig", "Zakhaev",
]

COOL_WORDS = [
    "Sniper", "Shadow", "Reaper", "Phantom", "Viper", "Wolf", "Ninja",
    "Assassin", "Blaze", "Storm", "Havoc", "Venom", "Ghost", "Raven",
    "Falcon", "Cobra", "Rex", "Titan", "Beast", "Killer", "Sniperz",
    "Hunter", "Slayer", "Reckless", "Rogue", "Nomad", "Rebel", "Outlaw",
    "Savage", "Vortex", "Nova", "Eclipse", "Blitz", "Fury", "Frostbite",
    "Warhead", "Ironclad", "Bulletproof", "Deadshot", "Ace", "Maverick",
    "Renegade", "Specter", "Wraith", "Grim", "Doom", "Apex", "Legend",
    "Crimson", "Onyx", "Rampage", "Sentinel", "Vandal", "Menace", "Toxic",
    "Glitch", "Static", "Overkill", "Bane", "Warlord", "Executioner",
]

PREFIXES = ["xXx_", "x_", "Th3_", "Real_", ""]
SUFFIXES = ["_xXx", "_YT", "_pro", "_TTV", ""]
PLATFORMS = ["PC", "Xbox", "PS"]


MAX_GAMERTAG = 25  # lungimea coloanei player.gamertag


def generate_gamertag(rng: random.Random) -> str:
    base = rng.choice(CHARACTER_NAMES) if rng.random() < 0.5 else rng.choice(COOL_WORDS)
    return f"{rng.choice(PREFIXES)}{base}{rng.choice(SUFFIXES)}"


def build_players(rng: random.Random, count: int) -> list[tuple[str, str]]:
    """Returnează `count` perechi (gamertag, platform). Sufixul `_i` garantează unicitatea."""
    players = []
    for i in range(count):
        suffix = f"_{i}"
        # player.gamertag e VARCHAR(25): tai baza, nu sufixul care garantează unicitatea
        gamertag = generate_gamertag(rng)[: MAX_GAMERTAG - len(suffix)] + suffix
        players.append((gamertag, rng.choice(PLATFORMS)))
    return players
