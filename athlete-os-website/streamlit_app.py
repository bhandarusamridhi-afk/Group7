"""
AthleteOS - Streamlit Community Cloud entry point.

A mock-up of a unified athlete performance platform that combines physical
(wearable/training) and mental (daily check-in) data into one decision surface.

Roles in this mock:
    - Athlete: personal readiness dashboard, trends, check-ins, recommendations.
    - Coach: single-sport squad dashboard, overtraining alerts, correlations.

Login is a mock role selector (no real authentication). All data is generated
in-memory at runtime and resets on refresh.
"""

from __future__ import annotations

import streamlit as st

from athleteos import APP_NAME, APP_TAGLINE, data
from athleteos.views import athlete_view, coach_view

st.set_page_config(
    page_title=f"{APP_NAME} — Athlete Performance",
    page_icon=":material/sprint:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Cached dataset (deterministic mock)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_dataset() -> dict:
    return data.build_dataset()


DATASET = load_dataset()


# --------------------------------------------------------------------------- #
# Session state for mock auth
# --------------------------------------------------------------------------- #
if "signed_in" not in st.session_state:
    st.session_state.signed_in = False
    st.session_state.role = None
    st.session_state.actor_id = None


def sign_out() -> None:
    st.session_state.signed_in = False
    st.session_state.role = None
    st.session_state.actor_id = None


# --------------------------------------------------------------------------- #
# Login screen (mock role selector)
# --------------------------------------------------------------------------- #
def login_screen() -> None:
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(f"# {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.markdown("##### Sign in to the demo")
        st.write("Pick a role and account to explore the mock dashboards.")

        role = st.radio("Role", ["Athlete", "Coach"], horizontal=True)

        if role == "Athlete":
            options = {a.name: a.id for a in DATASET["athletes"]}
            label = "Select athlete account"
        else:
            options = {c["name"]: c["id"] for c in DATASET["coaches"]}
            label = "Select coach account"

        choice = st.selectbox(label, list(options.keys()))

        if st.button("Sign in", type="primary", use_container_width=True):
            st.session_state.signed_in = True
            st.session_state.role = role
            st.session_state.actor_id = options[choice]
            st.rerun()

        st.divider()
        st.caption(
            "Mock authentication only — no passwords, no real data. "
            "Data is generated in-memory and resets on refresh."
        )


# --------------------------------------------------------------------------- #
# Authenticated app
# --------------------------------------------------------------------------- #
def app_shell() -> None:
    role = st.session_state.role
    actor_id = st.session_state.actor_id

    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        st.caption(APP_TAGLINE)
        st.divider()
        if role == "Athlete":
            athlete = data.get_athlete(DATASET, actor_id)
            st.markdown(f"**{athlete.name}**")
            st.caption(f"Athlete · {athlete.sport}")
        else:
            coach = data.get_coach(DATASET, actor_id)
            st.markdown(f"**{coach['name']}**")
            st.caption(f"Coach · {coach['sport']}")
        st.divider()
        st.button("Sign out", on_click=sign_out, use_container_width=True)
        st.caption("AthleteOS demo · mock data")

    if role == "Athlete":
        athlete = data.get_athlete(DATASET, actor_id)
        athlete_view.render(athlete)
    else:
        coach_view.render(DATASET, actor_id)


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
if st.session_state.signed_in:
    app_shell()
else:
    login_screen()
