"""
AthleteOS - Rule-based analytics engine.

Pure functions that derive readiness scores, overtraining alerts, correlations
and AI-style recommendations from an athlete's history. No external API keys
required, so everything runs offline on Streamlit Community Cloud.
"""

from __future__ import annotations

import pandas as pd

# Thresholds used for alerting (US-07).
STRESS_ALERT = 7.0          # daily stress index at/above this triggers alert
READINESS_ALERT = 45.0      # readiness below this triggers alert
HRV_DROP_PCT = 0.12         # >12% drop vs 7-day baseline triggers alert


def readiness_score(row: pd.Series) -> float:
    """
    Combine physical recovery + mental state into a single 0-100 readiness
    score. Higher is better / more ready to perform.
    """
    # Physical recovery component (0-100)
    sleep_component = min(row["sleep_hours"] / 8.0, 1.0) * 100
    quality_component = row["sleep_quality"]
    hrv_component = min(row["hrv"] / 80.0, 1.0) * 100
    # Lower resting HR is better; map 42-80 -> 100-0
    hr_component = max(0.0, min(100.0, (80 - row["resting_hr"]) / (80 - 42) * 100))
    physical = (
        0.30 * sleep_component
        + 0.20 * quality_component
        + 0.30 * hrv_component
        + 0.20 * hr_component
    )

    # Mental component (0-100). Stress is inverted (low stress = good).
    stress_inv = (10 - row["stress"]) * 10
    mental = (
        0.40 * stress_inv
        + 0.20 * (row["focus"] * 10)
        + 0.20 * (row["confidence"] * 10)
        + 0.20 * (row["motivation"] * 10)
    )

    # Acute training load penalty (very high load reduces readiness)
    load_penalty = max(0.0, (row["training_load"] - 90) * 0.5)

    score = 0.55 * physical + 0.45 * mental - load_penalty
    return round(max(0.0, min(100.0, score)), 1)


def enrich_history(df: pd.DataFrame) -> pd.DataFrame:
    """Add a derived `readiness` column + rolling acute:chronic load ratio."""
    out = df.copy()
    out["readiness"] = out.apply(readiness_score, axis=1)
    # Acute (7d) vs chronic (28d) load ratio - classic overtraining proxy.
    out["acute_load"] = out["training_load"].rolling(7, min_periods=1).mean()
    out["chronic_load"] = out["training_load"].rolling(28, min_periods=1).mean()
    out["acwr"] = (out["acute_load"] / out["chronic_load"]).round(2)
    return out


def latest(df: pd.DataFrame) -> pd.Series:
    return df.iloc[-1]


def compute_alerts(df: pd.DataFrame) -> list[dict]:
    """
    Return a list of active alerts for an athlete based on their latest day.
    Each alert: {level, title, detail}.
    """
    enriched = enrich_history(df)
    today = latest(enriched)
    alerts: list[dict] = []

    if today["readiness"] < READINESS_ALERT:
        alerts.append(
            {
                "level": "high",
                "title": "Low readiness",
                "detail": f"Readiness score is {today['readiness']:.0f}/100, "
                f"below the {READINESS_ALERT:.0f} intervention threshold.",
            }
        )

    if today["stress"] >= STRESS_ALERT:
        alerts.append(
            {
                "level": "high",
                "title": "Elevated stress index",
                "detail": f"Self-reported stress is {today['stress']:.1f}/10. "
                "Consider a check-in conversation.",
            }
        )

    # HRV drop vs 7-day baseline
    baseline_hrv = enriched["hrv"].iloc[-8:-1].mean() if len(enriched) > 7 else enriched["hrv"].mean()
    if baseline_hrv and today["hrv"] < baseline_hrv * (1 - HRV_DROP_PCT):
        drop = (1 - today["hrv"] / baseline_hrv) * 100
        alerts.append(
            {
                "level": "medium",
                "title": "HRV suppression",
                "detail": f"HRV is {drop:.0f}% below the 7-day baseline - a possible "
                "fatigue or illness signal.",
            }
        )

    # Acute:chronic workload ratio danger zone (>1.5)
    if today["acwr"] and today["acwr"] > 1.5:
        alerts.append(
            {
                "level": "medium",
                "title": "Spiking training load",
                "detail": f"Acute:chronic workload ratio is {today['acwr']:.2f} "
                "(>1.5 is associated with raised injury risk).",
            }
        )

    return alerts


def recommendations(df: pd.DataFrame) -> list[str]:
    """
    Rule-based 'AI' recommendations (US-09) derived from current readiness
    and the underlying signals driving it.
    """
    enriched = enrich_history(df)
    today = latest(enriched)
    recs: list[str] = []

    r = today["readiness"]
    if r >= 75:
        recs.append(
            "Readiness is high - a good day for a high-intensity or key technical "
            "session. Push toward peak training stimulus."
        )
    elif r >= 55:
        recs.append(
            "Readiness is moderate - proceed with the planned session but keep "
            "intensity controlled and monitor how you feel."
        )
    else:
        recs.append(
            "Readiness is low - prioritise active recovery, mobility, or a light "
            "aerobic session over high-intensity work today."
        )

    if today["sleep_hours"] < 6.5:
        recs.append(
            f"Sleep was only {today['sleep_hours']:.1f}h. Aim for 8h tonight and "
            "consider a short afternoon nap to support recovery."
        )
    if today["stress"] >= 6.5:
        recs.append(
            "Stress is elevated. Add a 10-minute breathing or mindfulness block "
            "before training to support focus."
        )
    if today["acwr"] and today["acwr"] > 1.4:
        recs.append(
            "Training load has spiked recently. Insert a deload or recovery day "
            "in the next 48 hours to reduce injury risk."
        )
    if today["motivation"] < 5:
        recs.append(
            "Motivation is dipping. Reconnect with a short-term goal or vary the "
            "session format to re-engage."
        )

    return recs


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation between mental metrics and physical output (US-08)."""
    enriched = enrich_history(df)
    cols = [
        "readiness",
        "training_load",
        "intensity",
        "sleep_hours",
        "hrv",
        "stress",
        "focus",
        "confidence",
        "motivation",
    ]
    return enriched[cols].corr().round(2)


def squad_summary(athletes, build_row_fn) -> pd.DataFrame:
    """Build a one-row-per-athlete summary table for the coach squad view."""
    return pd.DataFrame([build_row_fn(a) for a in athletes])
