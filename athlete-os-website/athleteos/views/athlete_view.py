"""Athlete-facing dashboard (US-02, US-03, US-04, US-05, US-09)."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from athleteos import analytics


def _readiness_color(score: float) -> str:
    if score >= 75:
        return "#16a34a"  # green
    if score >= 55:
        return "#d97706"  # amber
    return "#dc2626"      # red


def _metric_delta(df: pd.DataFrame, col: str) -> float:
    if len(df) < 2:
        return 0.0
    return round(float(df[col].iloc[-1] - df[col].iloc[-2]), 1)


def render(athlete) -> None:
    df = analytics.enrich_history(athlete.history)
    today = analytics.latest(df)

    # ---- Header ----------------------------------------------------------- #
    st.markdown(f"### {athlete.name}")
    st.caption(f"{athlete.sport}  ·  Age {athlete.age}")

    wear_col1, wear_col2 = st.columns([1, 4])
    with wear_col1:
        if athlete.wearable_connected:
            st.success(f"{athlete.wearable} connected", icon=":material/watch:")
        else:
            st.warning(f"{athlete.wearable} not synced", icon=":material/watch_off:")
    st.divider()

    # ---- Readiness hero --------------------------------------------------- #
    score = today["readiness"]
    color = _readiness_color(score)
    hero_l, hero_r = st.columns([1, 2])
    with hero_l:
        st.markdown(
            f"""
            <div style="text-align:center;padding:1.2rem;border-radius:16px;
                        background:{color}1a;border:1px solid {color}40;">
                <div style="font-size:0.85rem;letter-spacing:0.08em;
                            text-transform:uppercase;color:{color};">Readiness</div>
                <div style="font-size:3.4rem;font-weight:700;color:{color};
                            line-height:1.1;">{score:.0f}</div>
                <div style="font-size:0.8rem;color:{color};">out of 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_r:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sleep", f"{today['sleep_hours']:.1f}h", _metric_delta(df, "sleep_hours"))
        c2.metric("HRV", f"{today['hrv']:.0f} ms", _metric_delta(df, "hrv"))
        c3.metric("Resting HR", f"{today['resting_hr']:.0f} bpm", _metric_delta(df, "resting_hr"))
        c4.metric("Stress", f"{today['stress']:.1f}/10", _metric_delta(df, "stress"),
                  delta_color="inverse")

    # ---- Alerts ----------------------------------------------------------- #
    alerts = analytics.compute_alerts(athlete.history)
    if alerts:
        for a in alerts:
            icon = ":material/error:" if a["level"] == "high" else ":material/warning:"
            st.warning(f"**{a['title']}** — {a['detail']}", icon=icon)

    st.divider()

    # ---- Trends ----------------------------------------------------------- #
    st.markdown("#### Trends")
    tab1, tab2, tab3 = st.tabs(["Readiness", "Training load", "Mental check-in"])

    with tab1:
        fig = px.area(df, x="date", y="readiness", range_y=[0, 100])
        fig.update_traces(line_color="#2563eb", fillcolor="rgba(37,99,235,0.15)")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis_title="Readiness", xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.bar(df, x="date", y="training_load", color="session_type")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis_title="Load", xaxis_title=None, legend_title=None)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        mental = df.melt(
            id_vars="date",
            value_vars=["stress", "focus", "confidence", "motivation"],
            var_name="metric",
            value_name="score",
        )
        fig = px.line(mental, x="date", y="score", color="metric", range_y=[0, 10])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis_title="Score (1-10)", xaxis_title=None, legend_title=None)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---- AI recommendations ---------------------------------------------- #
    st.markdown("#### Today's recommendations")
    for rec in analytics.recommendations(athlete.history):
        st.markdown(f"- {rec}")

    st.divider()

    # ---- Daily mental check-in (mock form, < 60s) ------------------------- #
    st.markdown("#### Daily mental check-in")
    st.caption("Takes under 60 seconds. (Mock: values reset on app refresh.)")
    with st.form(f"checkin_{athlete.id}"):
        f1, f2 = st.columns(2)
        stress = f1.slider("Stress", 1, 10, int(round(today["stress"])))
        focus = f2.slider("Focus", 1, 10, int(round(today["focus"])))
        confidence = f1.slider("Confidence", 1, 10, int(round(today["confidence"])))
        motivation = f2.slider("Motivation", 1, 10, int(round(today["motivation"])))
        submitted = st.form_submit_button("Submit check-in", type="primary")
        if submitted:
            st.success(
                f"Check-in logged for {dt.date.today():%b %d}. "
                f"Stress {stress} · Focus {focus} · Confidence {confidence} · "
                f"Motivation {motivation}."
            )

    # ---- Training load logging (mock form) -------------------------------- #
    st.markdown("#### Log a training session")
    with st.form(f"trainlog_{athlete.id}"):
        t1, t2, t3 = st.columns(3)
        s_type = t1.selectbox(
            "Type", ["Endurance", "Strength", "Speed", "Recovery", "Technical", "Rest"]
        )
        duration = t2.number_input("Duration (min)", 0, 240, 75, step=5)
        intensity = t3.slider("Intensity", 0, 10, 6)
        logged = st.form_submit_button("Log session", type="primary")
        if logged:
            st.success(
                f"Logged {s_type} session · {duration} min · intensity {intensity}/10."
            )
