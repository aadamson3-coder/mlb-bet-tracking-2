import requests

BASE_URL = "https://statsapi.mlb.com/api/v1"


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_team_stats(team_id, season):
    url = f"{BASE_URL}/teams/{team_id}/stats"

    params = {
        "stats": "season",
        "group": "hitting",
        "season": season,
    }

    return get_json(url, params)


def get_pitcher_stats(player_id, season):
    if not player_id:
        return {}

    url = f"{BASE_URL}/people/{player_id}/stats"

    params = {
        "stats": "season",
        "group": "pitching",
        "season": season,
    }

    return get_json(url, params)


def get_recent_games(team_id):
    url = f"{BASE_URL}/schedule"

    params = {
        "sportId": 1,
        "teamId": team_id,
        "hydrate": "team",
    }

    return get_json(url, params)


def get_roster(team_id):
    url = f"{BASE_URL}/teams/{team_id}/roster"
    return get_json(url)


def get_player(player_id):
    url = f"{BASE_URL}/people/{player_id}"
    return get_json(url)


def get_game_feed(game_pk):
    url = f"{BASE_URL}/game/{game_pk}/feed/live"
    return get_json(url)
