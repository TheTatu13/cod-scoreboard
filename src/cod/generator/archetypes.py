"""Arhetipuri de jucători: fiecare are un interval de skill (cât de bine omoară) și de support
(cât de des e asistent). Ponderile fac ca majoritatea să fie 'Recrut' (K/D în jur de 1), iar
câțiva să fie outlieri. Valorile sunt alegerea mea de pornire: schimbă-le după gust.
"""

import random

# nume: (pondere, skill_min, skill_max, support_min, support_max)
ARCHETYPES = {
    "Recrut":     (40, 0.7, 1.1, 0.5, 1.2),
    "Smoker":     (12, 0.8, 1.2, 1.2, 1.9),
    "Mohawk":     (10, 0.9, 1.3, 0.6, 1.2),
    "Number":     (8,  1.0, 1.4, 0.6, 1.2),
    "Ramirez":    (8,  1.0, 1.4, 0.8, 1.4),
    "Menendez":   (6,  1.1, 1.5, 0.5, 1.1),
    "No Russian": (6,  0.6, 1.3, 0.3, 1.0),
    "Insanity":   (5,  0.5, 2.0, 0.3, 1.0),
    "Ghost":      (3,  1.3, 1.7, 0.4, 1.0),
    "Demon":      (2,  1.5, 1.9, 0.4, 1.0),
}


def assign_archetypes(rng: random.Random, player_ids: list[int]) -> dict[int, str]:
    names = list(ARCHETYPES)
    weights = [ARCHETYPES[n][0] for n in names]
    return {p: rng.choices(names, weights=weights)[0] for p in player_ids}


def roll_abilities(rng: random.Random, archetype: str) -> tuple[float, float]:
    _, s_lo, s_hi, a_lo, a_hi = ARCHETYPES[archetype]
    return rng.uniform(s_lo, s_hi), rng.uniform(a_lo, a_hi)
