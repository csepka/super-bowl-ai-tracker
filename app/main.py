from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.config import settings

# Project root: same folder as app/ and .env (works no matter where uvicorn is run from)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
from app.data_sources import fetch_state, demo_get_index, demo_set_index
from app.game_logic import (
    fingerprint,
    kickoff_countdown,
    compute_win_prob_simple,
    game_phase,
)
from app.store import STORE
from app.ai_engine import (
    ai_live_commentary,
    ai_winprob_explain,
    ai_postgame_recap,
)
from app.persist import load_state, save_state
from app.assets import team_logo_url

app = FastAPI(title="Super Bowl AI Tracker")
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "app" / "templates"))


@app.on_event("startup")
def startup():
    import logging
    # Reduce terminal spam from /api/state and /api/settings (called every few seconds)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    if settings.gemini_api_key:
        print("Gemini API key loaded. AI commentary enabled.")
    else:
        print("WARNING: GEMINI_API_KEY not set. Put your key in .env in the project root. AI will show placeholder text.")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


RATE_LIMIT_MSG = "rate limit"

def _dedupe_insert(buf: list[str], text: str, max_items: int = 50) -> None:
    t = (text or "").strip()
    if not t or RATE_LIMIT_MSG in t.lower():
        return
    nt = _norm(t)
    for existing in buf[:10]:
        if _norm(existing) == nt:
            return
    buf.insert(0, t)
    del buf[max_items:]


def _asset_payload(state: dict | None) -> dict:
    away = (state or {}).get("away_team", settings.away_team)
    home = (state or {}).get("home_team", settings.home_team)
    return {
        "away_logo": team_logo_url(away),
        "home_logo": team_logo_url(home),
    }


def _default_state() -> dict:
    return {
        "home_team": settings.home_team,
        "away_team": settings.away_team,
        "home_score": 0,
        "away_score": 0,
        "status": "pregame",
        "quarter": None,
        "clock": None,
        "phase": "PREGAME",
    }


def _payload() -> dict:
    raw = STORE.last_state or _default_state()
    state = {
        **raw,
        "home_score": int(raw.get("home_score", 0) or 0),
        "away_score": int(raw.get("away_score", 0) or 0),
        "phase": raw.get("phase") or ("FINAL" if raw.get("status") == "final" else "LIVE" if raw.get("status") == "live" else "PREGAME"),
    }
    assets = _asset_payload(state)
    return {
        "state": state,
        "commentary": STORE.commentary[:20],
        "winprob_home": STORE.winprob_home,
        "winprob_history": STORE.winprob_history[:20],
        "postgame_recap": STORE.postgame_recap,
        "meta": {
            "poll_count": STORE.poll_count,
            "last_update_iso": STORE.last_update_iso,
            "demo_mode": settings.demo_mode,
            "live_mode": not settings.demo_mode,
            "espn_game_id_set": bool(settings.espn_game_id),
            "demo_idx": demo_get_index() if settings.demo_mode else None,
        },
        **assets,
    }


def _persist() -> None:
    save_state({
        "meta": {
            "demo_mode": settings.demo_mode,
            "demo_idx": demo_get_index() if settings.demo_mode else None,
        }
    })


def _hydrate_from_disk() -> None:
    saved = load_state()
    if not saved:
        return
    meta = saved.get("meta") or {}
    if settings.demo_mode and meta.get("demo_idx") is not None:
        demo_set_index(meta.get("demo_idx"))

    STORE.last_fingerprint = None
    STORE.commentary.clear()
    STORE.winprob_history.clear()
    STORE.winprob_home = None
    STORE.postgame_recap = None
    STORE.last_state = None
    STORE.poll_count = 0
    STORE.last_update_iso = None


_hydrate_from_disk()


async def poll_once() -> None:
    state_obj = await fetch_state()
    state = state_obj.to_dict()
    state["phase"] = game_phase(state_obj)
    STORE.last_state = state

    fp = fingerprint(state_obj)
    STORE.poll_count += 1
    STORE.last_update_iso = _now_iso()

    if STORE.last_fingerprint == fp:
        _persist()
        return
    STORE.last_fingerprint = fp

    _dedupe_insert(STORE.commentary, await ai_live_commentary({"state": state}))

    wp = compute_win_prob_simple(state_obj)
    STORE.winprob_home = wp
    expl = await ai_winprob_explain(state, wp)
    leader = state["home_team"] if wp >= 0.5 else state["away_team"]
    pct = int(wp * 100) if wp >= 0.5 else int((1 - wp) * 100)
    _dedupe_insert(STORE.winprob_history, f"{leader} {pct}% — {expl}")

    if state["status"] == "final" and STORE.postgame_recap is None:
        STORE.postgame_recap = await ai_postgame_recap(
            state,
            STORE.winprob_history[:10],
            [],
        )

    _persist()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if STORE.last_state is None:
        STORE.last_state = _default_state()

    state = STORE.last_state
    assets = _asset_payload(state)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "kickoff": settings.kickoff_iso,
            "countdown": kickoff_countdown(settings.kickoff_iso),
            "state": {**STORE.last_state, "home_score": STORE.last_state.get("home_score", 0) or 0, "away_score": STORE.last_state.get("away_score", 0) or 0},
            "commentary": STORE.commentary[:20],
            "winprob_history": STORE.winprob_history[:20],
            "winprob_home": STORE.winprob_home,
            "postgame_recap": STORE.postgame_recap,
            "meta": {"poll_count": STORE.poll_count, "last_update_iso": STORE.last_update_iso, "demo_mode": settings.demo_mode, "live_mode": not settings.demo_mode, "espn_game_id_set": bool(settings.espn_game_id)},
            **assets,
        },
    )


@app.post("/admin/demo/reset")
async def admin_demo_reset():
    """Reset demo to the start so 'Run full demo' plays from event 0."""
    if not settings.demo_mode:
        return JSONResponse({"ok": True, "message": "Not in demo mode"}, status_code=200)
    demo_set_index(0)
    STORE.last_fingerprint = None
    STORE.commentary.clear()
    STORE.winprob_history.clear()
    STORE.winprob_home = None
    STORE.postgame_recap = None
    STORE.last_state = _default_state()
    STORE.poll_count = 0
    STORE.last_update_iso = _now_iso()
    _persist()
    return JSONResponse({"ok": True, **_payload()})


@app.post("/admin/poll")
async def admin_poll():
    await poll_once()
    return JSONResponse({"ok": True, **_payload()})


@app.get("/api/state")
async def api_state():
    return JSONResponse(_payload())


@app.post("/admin/clear/{panel}")
async def clear_panel(panel: str):
    panel = panel.lower()
    if panel == "commentary":
        STORE.commentary.clear()
    elif panel == "winprob":
        STORE.winprob_history.clear()
        STORE.winprob_home = None
    elif panel == "recap":
        STORE.postgame_recap = None
    elif panel == "all":
        STORE.commentary.clear()
        STORE.winprob_history.clear()
        STORE.winprob_home = None
        STORE.postgame_recap = None
    else:
        raise HTTPException(
            status_code=400,
            detail="panel must be one of: commentary, winprob, recap, all",
        )

    STORE.last_update_iso = _now_iso()
    _persist()
    return JSONResponse({"ok": True, **_payload()})


@app.get("/api/settings")
async def api_settings():
    return JSONResponse({
        "demo_mode": settings.demo_mode,
        "live_mode": not settings.demo_mode,
        "espn_game_id_set": bool(settings.espn_game_id),
        "gemini_configured": bool(settings.gemini_api_key),
    })


@app.get("/api/debug")
async def api_debug():
    """Diagnostics: .env location, API key set, and a test Gemini call."""
    from app.ai_engine import _get_model, _generate
    env_path = PROJECT_ROOT / ".env"
    result = {
        "project_root": str(PROJECT_ROOT),
        "env_file_exists": env_path.exists(),
        "env_path": str(env_path),
        "gemini_configured": bool(settings.gemini_api_key),
    }
    if settings.gemini_api_key:
        try:
            test_response = _generate("Reply with exactly: OK", max_tokens=10)
            result["gemini_test"] = "ok" if "OK" in test_response or test_response.strip() else test_response
            result["gemini_error"] = None
        except Exception as e:
            result["gemini_test"] = None
            result["gemini_error"] = str(e)
    else:
        result["gemini_test"] = None
        result["gemini_error"] = "No API key"
    return JSONResponse(result)
