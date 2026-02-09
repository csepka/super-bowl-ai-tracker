from pathlib import Path
import os
from dotenv import load_dotenv

# Project root: folder containing app/ and .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def _load_env() -> None:
    load_dotenv(ENV_PATH)


def _clean_key(val: str | None) -> str | None:
    if not val or not isinstance(val, str):
        return None
    val = val.strip().strip('"').strip("'")
    return val if val else None


def get_gemini_api_key() -> str | None:
    """Read Gemini API key from .env at runtime so it always reflects the file."""
    _load_env()
    return _clean_key(os.getenv("GEMINI_API_KEY"))


def get_settings() -> dict:
    """Read all settings from env at runtime."""
    _load_env()
    return {
        "demo_mode": os.getenv("DEMO_MODE", "1") == "1",
        "kickoff_iso": os.getenv("KICKOFF_ISO", "2026-02-08T18:30:00-05:00") or "2026-02-08T18:30:00-05:00",
        "home_team": os.getenv("HOME_TEAM", "Patriots") or "Patriots",
        "away_team": os.getenv("AWAY_TEAM", "Seahawks") or "Seahawks",
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash") or "gemini-2.0-flash",
        "espn_game_id": os.getenv("ESPN_GAME_ID") or None,
    }


# Load once at import
_load_env()


class Settings:
    """Simple settings container; values read from env at import and via get_* for key."""

    def __init__(self) -> None:
        s = get_settings()
        self.demo_mode = s["demo_mode"]
        self.kickoff_iso = s["kickoff_iso"]
        self.home_team = s["home_team"]
        self.away_team = s["away_team"]
        self.gemini_model = s["gemini_model"]
        self.espn_game_id = s["espn_game_id"]

    @property
    def gemini_api_key(self) -> str | None:
        return get_gemini_api_key()


settings = Settings()
