# AthleteOS

A mock-up of a **unified athlete performance platform** that combines physical
(wearable + training load) and mental (daily check-in) data into a single
decision surface for athletes and coaches.

> This is a front-end mock-up built with **Streamlit**. All data is generated
> in-memory at runtime and resets on refresh — there is no database, no real
> authentication, and no external API keys required.

## Features

**Athlete dashboard**
- Unified readiness score (physical recovery + mental state)
- Sleep, HRV, resting HR, and stress KPIs with day-over-day deltas
- Readiness, training-load, and mental check-in trend charts
- Recovery / overtraining alerts
- Rule-based "AI" training recommendations
- 60-second daily mental check-in form + training session logging (mock)

**Coach dashboard**
- Single-sport squad view (a coach only ever sees athletes from **their own
  sport**)
- Squad KPIs (avg readiness, athletes at risk, active alerts)
- Per-athlete overtraining / recovery alerts
- Sortable squad readiness table + comparison chart
- Mental ↔ physical correlation analytics

## Roles

Login is a **mock role selector** (no passwords). Choose **Athlete** or
**Coach** and pick a demo account.

## Project structure

```
streamlit_app.py            # entry point (Streamlit Community Cloud runs this)
requirements.txt            # Python dependencies
.streamlit/config.toml      # theme
athleteos/
  __init__.py
  data.py                   # in-memory mock dataset (deterministic)
  analytics.py              # readiness, alerts, recommendations, correlations
  views/
    athlete_view.py         # athlete dashboard
    coach_view.py           # coach squad dashboard
```

## Run locally (optional)

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy on Streamlit Community Cloud (recommended)

1. Push this repository to **GitHub** (public or private).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **Create app → Deploy a public app from GitHub**.
4. Select your repository and branch, and set the **main file path** to:
   ```
   streamlit_app.py
   ```
5. Click **Deploy**. Streamlit installs `requirements.txt` automatically and
   builds the app.

That's it — no secrets or environment variables are needed for this mock.

## Develop in GitHub Codespaces (optional)

1. On your GitHub repo, click **Code → Codespaces → Create codespace**.
2. In the Codespace terminal:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```
3. Codespaces forwards the port and gives you a preview URL.

## Notes & scope

This mock implements the Must-Have and Should-Have athlete/coach stories from
the product requirements (training log, wearable status, daily check-in,
athlete dashboard, coach squad dashboard, overtraining alerts, correlation
analytics, and AI-style recommendations). Items explicitly out of scope for v1
(social feed, custom metric builder, video analysis, EHR integration) are not
included.
