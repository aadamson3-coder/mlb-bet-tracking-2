import requests
from utils import today_et

def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def get_schedule():
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1, "date": today_et(), "hydrate": "probablePitcher"}
    data = get_json(url, params=params)
    schedule = {}

    for day in data.get("dates", []):
        for game in day.get("games", []):
            away = game["teams"]["away"]["team"]["name"]
            home = game["teams"]["home"]["team"]["name"]
            key = f"{away} @ {home}"
            schedule[key] = {
                "away": away,
                "home": home,
                "away_pitcher": game["teams"]["away"].get("probablePitcher", {}).get("fullName", "TBD"),
                "home_pitcher": game["teams"]["home"].get("probablePitcher", {}).get("fullName", "TBD"),
                "game_time": game.get("gameDate", ""),
            }
    return schedule

def get_team_records():
    url = "https://statsapi.mlb.com/api/v1/standings"
    params = {"leagueId": "103,104"}
    data = get_json(url, params=params)
    records = {}

    for group in data.get("records", []):
        for tr in group.get("teamRecords", []):
            team = tr["team"]["name"]
            wins = int(tr.get("wins", 0))
            losses = int(tr.get("losses", 0))
            games = max(1, wins + losses)
            records[team] = {"wins": wins, "losses": losses, "win_pct": wins / games}

    return records
