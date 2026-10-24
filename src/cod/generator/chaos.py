"""Defecte injectate în feed-ul de evenimente (JSON), pentru partea de data quality.

MySQL rămâne curat (are FK-uri). Feed-ul JSON e „sursa murdară": aceleași kill-uri, dar cu
defectele pe care le întâlnești în date reale. Funcția `inject_chaos` e pură: același seed și
aceleași evenimente dau exact aceleași defecte, iar `manifest` spune care eveniment a fost stricat
și cum. Pipeline-ul de mai târziu trebuie să le găsească pe toate (asta e testul de data quality).

Defecte (un eveniment primește cel mult unul dintre primele cinci):
  orphan_victim   victim_id care nu există în player
  self_kill       killer_id = victim_id
  ts_out_of_range timestamp_in_match negativ sau mai mare decât durata meciului
  dirty_weapon    numele armei cu majuscule, spații sau literă schimbată
  missing_field   victim_id sau weapon lipsă (null)
Independent de ele:
  duplicate       același event_id emis de două ori
  late            evenimentul ajunge într-o zi de livrare ulterioară zilei în care s-a întâmplat
  schema_drift    de la o dată încolo, `is_headshot` se numește `headshot` și apare `client_version`
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ChaosConfig:
    orphan_victim: float = 0.005
    self_kill: float = 0.003
    ts_out_of_range: float = 0.004
    dirty_weapon: float = 0.03
    missing_field: float = 0.004
    duplicate: float = 0.02
    late: float = 0.03
    max_late_days: int = 3
    drift_after_fraction: float = 0.8  # ultimele 20% din zile au schema schimbată


DEFECTS = (
    "orphan_victim", "self_kill", "ts_out_of_range", "dirty_weapon", "missing_field",
    "duplicate", "late",
)


def _dirty_name(rng: random.Random, name: str) -> str:
    """Strică numele armei; garantat diferit de original (ex. 'M4A1'.upper() n-ar schimba nimic)."""
    while True:
        kind = rng.randint(0, 3)
        if kind == 0:
            dirty = name.upper()
        elif kind == 1:
            dirty = f"  {name} "
        elif kind == 2 and len(name) > 3:
            i = rng.randrange(len(name) - 1)
            dirty = name[:i] + name[i + 1] + name[i] + name[i + 2:]
        else:
            dirty = name.lower() + " "
        if dirty != name:
            return dirty


def inject_chaos(
    rng: random.Random,
    events: list[dict],
    cfg: ChaosConfig,
    *,
    max_player_id: int,
) -> tuple[list[tuple[date, dict]], dict]:
    """Returnează ([(zi_de_livrare, eveniment)], manifest).

    `events` trebuie să fie într-o ordine stabilă (ORDER BY event_id), altfel nu e determinist.
    """
    days = sorted({e["event_time"][:10] for e in events})
    drift_from = days[int(len(days) * cfg.drift_after_fraction)] if days else None

    out: list[tuple[date, dict]] = []
    defects: dict[str, list[str]] = {name: [] for name in DEFECTS}
    drifted = 0

    for original in events:
        e = dict(original)
        eid = e["event_id"]

        # defecte exclusive: o singură tragere, praguri cumulate
        r = rng.random()
        t = cfg.orphan_victim
        if r < t:
            e["victim_id"] = max_player_id + rng.randint(1, 5000)
            defects["orphan_victim"].append(eid)
        elif r < (t := t + cfg.self_kill):
            if e["killer_id"] is not None:
                e["killer_id"] = e["victim_id"]
                defects["self_kill"].append(eid)
        elif r < (t := t + cfg.ts_out_of_range):
            e["timestamp_in_match"] = (
                -rng.randint(1, 60) if rng.random() < 0.5
                else e["match_duration_sec"] + rng.randint(1, 600)
            )
            defects["ts_out_of_range"].append(eid)
        elif r < (t := t + cfg.dirty_weapon):
            e["weapon"] = _dirty_name(rng, e["weapon"])
            defects["dirty_weapon"].append(eid)
        elif r < (t := t + cfg.missing_field):
            e[rng.choice(["victim_id", "weapon"])] = None
            defects["missing_field"].append(eid)

        # livrare: ziua evenimentului, sau mai târziu dacă e „late"
        delivery = date.fromisoformat(e["event_time"][:10])
        if rng.random() < cfg.late:
            delivery += timedelta(days=rng.randint(1, cfg.max_late_days))
            defects["late"].append(eid)

        copies = 1
        if rng.random() < cfg.duplicate:
            copies = 2
            defects["duplicate"].append(eid)

        for _ in range(copies):
            row = dict(e)
            if drift_from and delivery.isoformat() >= drift_from:
                row["headshot"] = row.pop("is_headshot")
                row["client_version"] = "2.1"
                drifted += 1
            out.append((delivery, row))

    manifest = {
        "clean_events": len(events),
        "emitted_rows": len(out),
        "schema_drift": {
            "from": drift_from, "renamed": {"is_headshot": "headshot"},
            "added": ["client_version"], "rows": drifted,
        },
        "defects": {k: sorted(v) for k, v in defects.items()},
        "counts": {k: len(v) for k, v in defects.items()},
    }
    return out, manifest
