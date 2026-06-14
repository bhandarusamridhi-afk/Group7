"""
AthleteOS - Mock data layer.

All data is generated in-memory at runtime (seeded for stability) so the app
runs cleanly on Streamlit Community Cloud with no database or paid backend.

Key domain rule (per product spec):
    Every coach is responsible for exactly ONE sport, and every athlete
    assigned to that coach competes in the SAME sport. A coach never sees
    athletes from a different sport in their dashboard.
"""

from __future__ import annotations

import datetime as dt
import random
from dataclasses import dataclass, field

import pandas as pd

# Deterministic seed so the demo looks identical across reruns / sessions.
SEED = 42

# Number of past days of history to generate per athlete.
HISTORY_DAYS = 45


# --------------------------------------------------------------------------- #
# Static reference data
# --------------------------------------------------------------------------- #

# Each coach owns a single sport. Athletes inherit their coach's sport.
COACHES = [
    {"id": "coach_track", "name": "Coach Maria Lopez", "sport": "Track & Field"},
    {"id": "coach_swim", "name": "Coach David Chen", "sport": "Swimming"},
    {"id": "coach_ball", "name": "Coach Aisha Khan", "sport": "Basketball"},
]

# First names used to generate athletes per sport.
_NAME_POOL = {
    "Track & Field": ["Alex Rivera", "Jordan Blake", "Sam Okafor", "Nadia Petrov", "Leo Tanaka"],
    "Swimming": ["Mia Larsson", "Ethan Wright", "Sofia Marino", "Kai Nakamura", "Ruth Adeyemi"],
    "Basketball": ["Marcus Hill", "Tara Singh", "Diego Santos", "Hana Kim", "Omar Farouk"],
}


@dataclass
class Athlete:
    id: str
    name: str
    sport: str
    coach_id: str
    age: int
    wearable: str
    wearable_connected: bool
    history: pd.DataFrame = field(default_factory=pd.DataFrame)


# --------------------------------------------------------------------------- #
# Generation helpers
# --------------------------------------------------------------------------- #

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _generate_history(rng: random.Random, profile: str) -> pd.DataFrame:
    """
    Generate a per-day record of physical + mental signals for one athlete.

    `profile` nudges the baselines so the squad contains a mix of healthy,
    average, and at-risk (overtraining) athletes for a realistic dashboard.
    """
    today = dt.date.today()

    # Baselines per profile.
    if profile == "at_risk":
        base_stress, base_sleep, base_hrv, base_load = 7.0, 5.8, 48, 75
    elif profile == "strong":
        base_stress, base_sleep, base_hrv, base_load = 3.2, 8.0, 78, 55
    else:  # average
        base_stress, base_sleep, base_hrv, base_load = 4.8, 7.0, 62, 60

    rows = []
    for i in range(HISTORY_DAYS):
        day = today - dt.timedelta(days=(HISTORY_DAYS - 1 - i))

        # Physical / wearable signals
        sleep_hours = _clamp(rng.gauss(base_sleep, 0.8), 3.5, 10)
        sleep_quality = _clamp(rng.gauss(sleep_hours * 10, 6), 30, 100)
        resting_hr = _clamp(rng.gauss(58 - (base_hrv - 60) * 0.1, 3), 42, 80)
        hrv = _clamp(rng.gauss(base_hrv, 7), 25, 110)

        # Training load (volume * intensity proxy)
        training_load = _clamp(rng.gauss(base_load, 18), 0, 120)
        intensity = _clamp(rng.gauss(6.5, 1.5), 1, 10)
        duration_min = _clamp(rng.gauss(75, 25), 20, 180)
        session_type = rng.choice(
            ["Endurance", "Strength", "Speed", "Recovery", "Technical", "Rest"]
        )
        if session_type == "Rest":
            training_load *= 0.15
            intensity = 0
            duration_min = 0

        # Mental check-in (1-10 scales)
        stress = _clamp(rng.gauss(base_stress + (training_load - base_load) * 0.02, 1.2), 1, 10)
        focus = _clamp(rng.gauss(8 - (stress - 5) * 0.5, 1.2), 1, 10)
        confidence = _clamp(rng.gauss(7.5 - (stress - 5) * 0.4, 1.3), 1, 10)
        motivation = _clamp(rng.gauss(7.5 - (stress - 5) * 0.3, 1.3), 1, 10)

        rows.append(
            {
                "date": day,
                "training_load": round(training_load, 1),
                "intensity": round(intensity, 1),
                "duration_min": round(duration_min),
                "session_type": session_type,
                "sleep_hours": round(sleep_hours, 1),
                "sleep_quality": round(sleep_quality),
                "resting_hr": round(resting_hr),
                "hrv": round(hrv),
                "stress": round(stress, 1),
                "focus": round(focus, 1),
                "confidence": round(confidence, 1),
                "motivation": round(motivation, 1),
            }
        )

    df = pd.DataFrame(rows)
    return df


def _build_athletes(rng: random.Random) -> list[Athlete]:
    athletes: list[Athlete] = []
    profiles_cycle = ["strong", "average", "at_risk", "average", "strong"]
    wearables = ["Garmin", "Apple Watch", "Whoop", "Polar"]

    for coach in COACHES:
        sport = coach["sport"]
        names = _NAME_POOL[sport]
        for idx, name in enumerate(names):
            profile = profiles_cycle[idx % len(profiles_cycle)]
            connected = rng.random() > 0.2
            athlete = Athlete(
                id=f"{coach['id']}_a{idx}",
                name=name,
                sport=sport,  # same sport as the coach -> enforced here
                coach_id=coach["id"],
                age=rng.randint(18, 32),
                wearable=rng.choice(wearables),
                wearable_connected=connected,
                history=_generate_history(rng, profile),
            )
            athletes.append(athlete)
    return athletes


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def build_dataset() -> dict:
    """Build the full mock dataset. Deterministic via SEED."""
    rng = random.Random(SEED)
    athletes = _build_athletes(rng)
    return {
        "coaches": COACHES,
        "athletes": athletes,
    }


def athletes_for_coach(dataset: dict, coach_id: str) -> list[Athlete]:
    """
    Return only athletes belonging to this coach.

    Because each athlete's sport equals its coach's sport, the returned list
    is guaranteed to be single-sport.
    """
    return [a for a in dataset["athletes"] if a.coach_id == coach_id]


def get_coach(dataset: dict, coach_id: str) -> dict | None:
    return next((c for c in dataset["coaches"] if c["id"] == coach_id), None)


def get_athlete(dataset: dict, athlete_id: str) -> Athlete | None:
    return next((a for a in dataset["athletes"] if a.id == athlete_id), None)
