import requests
from datetime import datetime

BASE_URL = "https://statsapi.mlb.com/api/v1"


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def today():
    return datetime.now().strftime("%Y-%m-%d")


def get_schedule():

    url = f"{BASE_URL}/schedule"

    params = {
        "sportId": 1,
        "date": today(),
        "hydrate": "probablePitcher"
    }

    data = get_json(url, params)

    games = []

    for date in data.get("dates", []):

        for game in date.get("games", []):

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            home_pitcher = home.get("probablePitcher", {})
            away_pitcher = away.get("probablePitcher", {})

            games.append({

                "game_pk": game["gamePk"],

                "game_time": game["gameDate"],

                "home": home["team"]["name"],
                "away": away["team"]["name"],

                "home_id": home["team"]["id"],
                "away_id": away["team"]["id"],

                "home_pitcher": home_pitcher.get("fullName", "TBD"),
                "away_pitcher": away_pitcher.get("fullName", "TBD"),

                "home_pitcher_id": home_pitcher.get("id"),
                "away_pitcher_id": away_pitcher.get("id"),

                "venue": game["venue"]["name"],

                # model.py will populate this later
                "market": {}

            })

    return games


def get_team_records():

    url = f"{BASE_URL}/standings"

    params = {
        "leagueId": "103,104",
        "season": datetime.now().year
    }

    data = get_json(url, params)

    records = {}

    for division in data.get("records", []):

        for team in division.get("teamRecords", []):

            wins = int(team["wins"])
            losses = int(team["losses"])

            games = max(1, wins + losses)

            records[team["team"]["name"]] = {

                "wins": wins,
                "losses": losses,
                "win_pct": wins / games

            }

    return records
