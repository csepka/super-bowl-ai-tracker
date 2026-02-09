#!/usr/bin/env python3
"""
Find the Super Bowl (or any NFL game) and its ESPN game ID.
Use this to get ESPN_GAME_ID for .env when tracking the live Super Bowl.
"""
import httpx
import asyncio
from datetime import datetime


async def find_nfl_games():
    """Fetch NFL scoreboard from ESPN (includes Super Bowl when in season)."""
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        events = data.get("events", [])

        if not events:
            print("No NFL games found. Try again during the season or Super Bowl Sunday.")
            return

        print(f"\n{'='*80}")
        print(f"NFL Games — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        for event in events:
            game_id = event.get("id")
            name = event.get("name", "Unknown")
            short_name = event.get("shortName", "")
            status = event.get("status", {})
            status_type = status.get("type", {}).get("state", "pre")
            status_detail = status.get("type", {}).get("detail", "Scheduled")

            competitions = event.get("competitions", [{}])
            comp = competitions[0] if competitions else {}
            competitors = comp.get("competitors", [])

            home = next((c for c in competitors if c.get("homeAway") == "home"), {})
            away = next((c for c in competitors if c.get("homeAway") == "away"), {})

            home_team = home.get("team", {}).get("displayName", "?")
            away_team = away.get("team", {}).get("displayName", "?")
            home_score = home.get("score", "0")
            away_score = away.get("score", "0")

            if status_type == "in":
                status_icon = "🔴 LIVE"
            elif status_type == "post":
                status_icon = "✅ FINAL"
            else:
                status_icon = "⏰ SCHEDULED"

            sb_tag = " 🏆 SUPER BOWL" if "super" in name.lower() or "super bowl" in short_name.lower() else ""
            print(f"{status_icon}{sb_tag} {short_name or name}")
            print(f"  Game ID: {game_id}")
            print(f"  {away_team} @ {home_team}")
            print(f"  Score: {away_score} - {home_score}")
            print(f"  Status: {status_detail}")
            if status_type == "in":
                period = status.get("period")
                clock = status.get("displayClock", "")
                print(f"  Q{period} - {clock}")
            print()

        first_id = events[0].get("id")
        print(f"To track this game, set in .env:")
        print(f"  ESPN_GAME_ID={first_id}")
        print(f"  DEMO_MODE=0")
        print()

    except Exception as e:
        print(f"Error fetching NFL games: {e}")


if __name__ == "__main__":
    asyncio.run(find_nfl_games())
