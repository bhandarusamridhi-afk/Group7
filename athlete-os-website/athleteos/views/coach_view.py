"""
Coach-facing dashboard (US-06, US-07, US-08).

Squad rule: a coach only ever sees athletes from THEIR OWN sport. This is
guaranteed by the data layer (athletes inherit their coach's sport) and we
re-assert it here defensively before rendering.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from athleteos import analytics, data


def _status_label(score: float) -> str:
    if score >= 75:
        return "Ready"
    if score >= 55:
        return "Monitor"
    return "At risk"


def _squad_row(athlete) -> dict:
    df = analytics.enrich_history(athlete.history)
    today = analytics.latest(df)
    alerts = analytics.compute_alerts(athlete.history)
    return {
        "Athlete": athlete.name,
        "Sport": athlete.sport,
        "Readiness": today["readiness"],
        "Status": _status_label(today["readiness"]),
        "Stress": today["stress"],
        "Sleep (h)": today["sleep_hours"],
        "HRV": today["hrv"],
        "ACWR": today["acwr"],
        "Alerts": len(alerts),
    }


def render(dataset: dict, coach_id: str) -> None:
    coach = data.get_coach(dataset, coach_id)
    squad = data.athletes_for_coach(dataset, coach_id)

    # Defensive single-sport guarantee.
    squad = [a for a in squad if a.sport == coach["sport"]]

    st.markdown(f"### {coach['name']}")
    st.caption(f"Squad sport: **{coach['sport']}**  ·  {len(squad)} athletes")
    st.divider()

    summary = analytics.squad_summary(squad, _squad_row)

    # ---- Squad KPIs ------------------------------------------------------- #
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Squad size", len(summary))
    k2.metric("Avg readiness", f"{summary['Readiness'].mean():.0f}")
    k3.metric("Athletes at risk", int((summary["Status"] == "At risk").sum()))
    k4.metric("Active alerts", int(summary["Alerts"].sum()))

    # ---- Overtraining / recovery alerts (US-07) --------------------------- #
    st.markdown("#### Alerts & interventions")
    any_alert = False
    for athlete in squad:
        alerts = analytics.compute_alerts(athlete.history)
        if not alerts:
            continue
        any_alert = True
        with st.expander(f"{athlete.name} — {len(alerts)} alert(s)", expanded=False):
            for a in alerts:
                icon = ":material/error:" if a["level"] == "high" else ":material/warning:"
                st.warning(f"**{a['title']}** — {a['detail']}", icon=icon)
    if not any_alert:
        st.success("No active alerts across the squad.", icon=":material/check_circle:")

    st.divider()

    # ---- Squad comparison table (US-06) ----------------------------------- #
    st.markdown("#### Squad readiness")
    styled = summary.sort_values("Readiness").reset_index(drop=True)
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Readiness": st.column_config.ProgressColumn(
                "Readiness", min_value=0, max_value=100, format="%d"
            ),
        },
    )

    # ---- Readiness bar comparison ----------------------------------------- #
    fig = px.bar(
        summary.sort_values("Readiness"),
        x="Readiness",
        y="Athlete",
        orientation="h",
        color="Status",
        color_discrete_map={"Ready": "#16a34a", "Monitor": "#d97706", "At risk": "#dc2626"},
        range_x=[0, 100],
    )
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), legend_title=None)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---- Correlation analytics (US-08) ------------------------------------ #
    st.markdown("#### Correlation analytics")
    st.caption("How mental metrics relate to physical output across the squad.")
    athlete_names = [a.name for a in squad]
    selected = st.selectbox("Select athlete", athlete_names)
    sel_athlete = next(a for a in squad if a.name == selected)
    corr = analytics.correlation_matrix(sel_athlete.history)
    fig_corr = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        aspect="auto",
    )
    fig_corr.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_corr, use_container_width=True)
