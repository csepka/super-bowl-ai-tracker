import json
from pathlib import Path
import httpx
from app.game_logic import GameState
from app.config import settings

_project_root = Path(__file__).resolve().parent.parent
DEMO_PATH = _project_root / "demo_data" / "demo_events.json"


class DemoFeed:
    def __init__(self):
        self.idx = 0
        self.events = json.loads(DEMO_PATH.read_text(encoding="utf-8"))

    def set_index(self, i: int) -> None:
        try:
            i = int(i)
        except Exception:
            return
        if i < 0:
            i = 0
        if i > len(self.events):
            i = len(self.events)
        self.idx = i

    def get_index(self) -> int:
        return int(self.idx)

    def next_state(self) -> GameState:
        e = self.events[min(self.idx, len(self.events) - 1)]
        self.idx += 1
        return GameState(
            home_team=settings.home_team,
            away_team=settings.away_team,
            home_score=e.get("home_score", 0),
            away_score=e.get("away_score", 0),
            status=e.get("status", "pregame"),
            quarter=e.get("quarter"),
            clock=e.get("clock"),
        )


_demo = DemoFeed()


def demo_get_index() -> int:
    return _demo.get_index()


def demo_set_index(i: int) -> None:
    _demo.set_index(i)


async def fetch_live_espn_state() -> GameState:
    """Fetch live game data from ESPN NFL API."""
    if not settings.espn_game_id:
        return GameState(settings.home_team, settings.away_team)

    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={settings.espn_game_id}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        competitions = data.get("competitions", [])
        if not competitions:
            header = data.get("header", {})
            competitions = header.get("competitions", [])

        if not competitions:
            return GameState(settings.home_team, settings.away_team)

        competition = competitions[0]
        competitors = competition.get("competitors", [])

        home_competitor = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away_competitor = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_team = home_competitor.get("team", {}).get("displayName", settings.home_team)
        away_team = away_competitor.get("team", {}).get("displayName", settings.away_team)
        home_score = int(home_competitor.get("score", 0))
        away_score = int(away_competitor.get("score", 0))

        status_detail = competition.get("status", {})
        status_type = status_detail.get("type", {}).get("state", "pre").lower()

        if status_type in ["pre", "scheduled"]:
            status = "pregame"
        elif status_type in ["in", "inprogress"]:
            status = "live"
        elif status_type in ["post", "final", "complete"]:
            status = "final"
        else:
            status = "pregame"

        period = status_detail.get("period")
        clock = status_detail.get("displayClock")

        return GameState(
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            status=status,
            quarter=period,
            clock=clock,
        )

    except Exception as e:
        print(f"Error fetching NFL data from ESPN: {e}")
        return GameState(settings.home_team, settings.away_team)


async def fetch_state() -> GameState:
    if settings.demo_mode:
        return _demo.next_state()
    return await fetch_live_espn_state()
