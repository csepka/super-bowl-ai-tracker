"""
Gemini-powered AI commentary for Super Bowl tracker.
Requires GEMINI_API_KEY in .env.
"""
from __future__ import annotations

import json
from app.config import settings

# Lazy init to avoid import-time API key requirement
_genai = None
_model = None


def _get_model():
    global _genai, _model
    if _model is not None:
        return _model
    if not settings.gemini_api_key:
        return None
    import google.generativeai as genai
    genai.configure(api_key=settings.gemini_api_key)
    _genai = genai
    _model = genai.GenerativeModel(settings.gemini_model)
    return _model


def _generate(prompt: str, max_tokens: int = 150) -> str:
    model = _get_model()
    if not model:
        return "[Set GEMINI_API_KEY in .env for AI commentary.]"
    try:
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.7},
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "rate" in err.lower():
            return "[Gemini rate limit — try again in a minute.]"
        if len(err) > 120:
            return "[Gemini error. Check API key and quota.]"
        return f"[Gemini error: {err}]"
    return "[No response]"


async def ai_live_commentary(event: dict) -> str:
    s = event.get("state", {})
    state_json = json.dumps(s, indent=0)
    prompt = f"""You are a concise, energetic Super Bowl commentator. In 1-2 short sentences, describe the current game situation. Be specific and vivid. No preamble.

Game state (JSON):
{state_json}

Commentary (1-2 sentences):"""
    return _generate(prompt, max_tokens=120)


async def ai_winprob_explain(state: dict, wp: float) -> str:
    home = state.get("home_team", "Home")
    away = state.get("away_team", "Away")
    leader = home if wp >= 0.5 else away
    pct = int(wp * 100) if wp >= 0.5 else int((1 - wp) * 100)
    q = state.get("quarter")
    clock = state.get("clock", "")

    prompt = f"""Super Bowl win-probability explainer. One short sentence only: why {leader} is at ~{pct}% (Q{q}, {clock}). Be specific.

One sentence:"""
    return _generate(prompt, max_tokens=60)


async def ai_postgame_recap(
    final_state: dict,
    winprob_history: list[str],
    player_notes: list[str],
) -> str:
    home = final_state["home_team"]
    away = final_state["away_team"]
    hs = final_state["home_score"]
    ays = final_state["away_score"]
    winner = home if hs > ays else away
    loser = away if winner == home else home
    winning_score = max(hs, ays)
    losing_score = min(hs, ays)

    context = (
        f"Final: {winner} {winning_score}, {loser} {losing_score}. "
        f"Recent win-prob notes: {'; '.join(winprob_history[:5])}."
    )
    prompt = f"""You are a Super Bowl recap writer. In 2-3 sentences, write a vivid, punchy recap of the game. Mention the winner and score; add one memorable angle (comeback, MVP moment, etc.). No bullet points.

{context}

Recap (2-3 sentences):"""
    return _generate(prompt, max_tokens=200)
