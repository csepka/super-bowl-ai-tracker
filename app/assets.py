from __future__ import annotations
import os

# Default team logos (NFL) - Seahawks vs Patriots
DEFAULT_TEAM_LOGOS = {
    "seahawks": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Seattle_Seahawks_logo.svg/330px-Seattle_Seahawks_logo.svg.png",
    "patriots": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/New_England_Patriots_logo.svg/330px-New_England_Patriots_logo.svg.png",
    "new england patriots": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/New_England_Patriots_logo.svg/330px-New_England_Patriots_logo.svg.png",
}


def _k(s: str) -> str:
    return (s or "").strip().lower()


def team_logo_url(team_name: str) -> str | None:
    key = _k(team_name)
    env_key = f"TEAM_LOGO_{key.replace(' ', '_').upper().replace('.', '')}"
    if os.getenv(env_key):
        return os.getenv(env_key)
    return DEFAULT_TEAM_LOGOS.get(key)


