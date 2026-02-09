# Super Bowl AI Tracker
<p align="center">
  <img width="1266" height="585" alt="IMG_5635" src="https://github.com/user-attachments/assets/c167b7d5-13b6-4444-86d3-797cc9103d51" />
  <br>
  <img width="910" height="318" alt="SUPER BOWL AI TRACKER" src="https://github.com/user-attachments/assets/78c71d56-962b-484e-8fee-c6ab10a648f0" />
</p>




An extension of [cfp-ai-tracker](https://github.com/csepka/cfp-ai-tracker) for the **Super Bowl—the largest sporting event in history**. Event-driven NFL tracker with **Gemini-powered live commentary**: same FSM (PREGAME → LIVE → FINAL), edge-triggered updates, and win-probability model, now using the **Gemini API** for all commentary and postgame recap.

## Features

- **ESPN NFL API** — Live game data (score, quarter, clock, player stats)
- **Gemini API** — AI commentary, win-probability explanations, QB analysis, postgame recap
- **Finite state machine** — PREGAME → LIVE → FINAL with edge-triggered updates
- **Demo mode** — Step through pre-recorded events without an ESPN game ID

## Quick Start

### 1. Install dependencies

```bash
cd super-bowl-ai-tracker
pip install -e .
# or: pip install fastapi uvicorn jinja2 httpx python-dotenv pydantic google-generativeai
```

### 2. Set your Gemini API key

Create a `.env` file (see `.env.example`):

```bash
GEMINI_API_KEY=your_api_key_here
DEMO_MODE=1
HOME_TEAM=Patriots
AWAY_TEAM=Seahawks
```

Get an API key at [Google AI Studio](https://aistudio.google.com/apikey).

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

### 4. Track the game

- **Demo mode** (`DEMO_MODE=1`): Click **Run full demo** or **Poll Now** to step through demo events; Gemini generates commentary.
- **Live real-time game** (`DEMO_MODE=0`): Set `ESPN_GAME_ID` in `.env` (see below), restart the server, then open the app—it will auto-refresh from ESPN every 10 seconds and show live score, clock, and Gemini commentary.

## Finding the Super Bowl game ID (for live mode)

When the Super Bowl (or any NFL game) is scheduled or live, run:

```bash
python find_super_bowl.py
```

This prints all current NFL games and their ESPN game IDs. Put the desired ID in `.env`:

```bash
DEMO_MODE=0
ESPN_GAME_ID=401547403
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | **Required** for AI. From [Google AI Studio](https://aistudio.google.com/apikey). |
| `GEMINI_MODEL` | Optional. Default: `gemini-2.0-flash`. |
| `DEMO_MODE` | `1` = demo data, `0` = live ESPN NFL. |
| `ESPN_GAME_ID` | ESPN event ID when `DEMO_MODE=0`. |
| `HOME_TEAM` / `AWAY_TEAM` | Default team names (e.g. Patriots, Seahawks). |
| `KICKOFF_ISO` | ISO datetime for countdown (e.g. `2026-02-08T18:30:00-05:00`). |

## Publishing this repo (keep your API key private)

- **Never commit `.env`.** It’s in `.gitignore`; it holds your `GEMINI_API_KEY` and `ESPN_GAME_ID`.
- Before you push, run:  
  `git status`  
  and confirm **`.env` does not appear** in the list. If it does, run `git reset HEAD .env` and do not add it.
- Share setup with others via **`.env.example`** only (no real keys). They copy it to `.env` and add their own key.
- If you ever committed `.env` in the past, remove it from the repo and rewrite history (e.g. `git filter-branch` or BFG) and rotate your API key.

## API

- `GET /` — Web UI
- `GET /api/state` — Current state JSON (state, commentary, winprob_history, postgame_recap)
- `POST /admin/poll` — Fetch latest game state and run Gemini commentary
- `POST /admin/clear/{panel}` — Clear panel: `commentary`, `winprob`, `recap`, or `all`

## Project layout

```
super-bowl-ai-tracker/
├── app/
│   ├── main.py          # FastAPI app, routes, poll logic
│   ├── config.py        # Settings from .env (Gemini, ESPN, teams)
│   ├── ai_engine.py     # Gemini: commentary, player watch, recap
│   ├── data_sources.py  # Demo feed + ESPN NFL summary API
│   ├── game_logic.py    # GameState, fingerprint, win prob, FSM
│   ├── store.py         # In-memory state (commentary, notes, recap)
│   ├── persist.py       # Demo index persistence
│   ├── assets.py        # Team/player image URLs
│   ├── templates/       # index.html
│   └── static/
├── demo_data/
│   └── demo_events.json # Demo game events
├── find_super_bowl.py   # List NFL games and get ESPN_GAME_ID
├── pyproject.toml
├── .env.example
└── README.md
```

Built as an extension of [cfp-ai-tracker](https://github.com/csepka/cfp-ai-tracker), with NFL + Gemini.
