from datetime import datetime, timedelta
from config import ET
from mlb_schedule import get_json

def recent_team_form(days=14):
    end = datetime.now(ET).date()
    start = end - timedelta(days=days)
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "startDate": start.strftime("%Y-%m-%d"), "endDate": end.strftime("%Y-%m-%d")}
    data = get_json(url, params=params)
    stats = {}

    for day in data.get("dates", []):
        for game in day.get("games", []):
            if game.get("status", {}).get("detailedState") != "Final":
                continue
            away = game["teams"]["away"]["team"]["name"]
            home = game["teams"]["home"]["team"]["name"]
            away_runs = int(game["teams"]["away"].get("score", 0))
            home_runs = int(game["teams"]["home"].get("score", 0))

            for team in [away, home]:
                stats.setdefault(team, {"games": 0, "wins": 0, "run_diff": 0})

            stats[away]["games"] += 1
            stats[home]["games"] += 1
            stats[away]["run_diff"] += away_runs - home_runs
            stats[home]["run_diff"] += home_runs - away_runs

            if away_runs > home_runs:
                stats[away]["wins"] += 1
            elif home_runs > away_runs:
                stats[home]["wins"] += 1

    return {
        team: {
            "recent_win_pct": s["wins"] / max(1, s["games"]),
            "recent_run_diff_per_game": s["run_diff"] / max(1, s["games"]),
            "recent_games": s["games"],
        }
        for team, s in stats.items()
    }
