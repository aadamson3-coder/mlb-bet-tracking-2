import requests
BASE_URL = "https://statsapi.mlb.com/api/v1"

def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def get_team_stats(team_id, season):
    return get_json(f"{BASE_URL}/teams/{team_id}/stats", {"stats":"season","group":"hitting","season":season})

def get_team_pitching_stats(team_id, season):
    return get_json(f"{BASE_URL}/teams/{team_id}/stats", {"stats":"season","group":"pitching","season":season})

def get_pitcher_stats(player_id, season):
    if not player_id: return {}
    return get_json(f"{BASE_URL}/people/{player_id}/stats", {"stats":"season","group":"pitching","season":season})

def get_pitcher_game_log(player_id, season):
    if not player_id: return {}
    return get_json(f"{BASE_URL}/people/{player_id}/stats", {"stats":"gameLog","group":"pitching","season":season})

def get_recent_games(team_id, start_date=None, end_date=None, season=None):
    params = {"sportId":1, "teamId": team_id}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    if season: params["season"] = season
    return get_json(f"{BASE_URL}/schedule", params)

def get_roster(team_id):
    return get_json(f"{BASE_URL}/teams/{team_id}/roster")

def get_player(player_id):
    return get_json(f"{BASE_URL}/people/{player_id}")

def get_game_feed(game_pk):
    return get_json(f"{BASE_URL}/game/{game_pk}/feed/live")
def get_team_hitting_splits(team_id, season, pitcher_hand):
    # pitcher_hand should be "L" or "R"
    sit_code = "vl" if pitcher_hand == "L" else "vr"

    url = f"{BASE_URL}/teams/{team_id}/stats"

    params = {
        "stats": "statSplits",
        "group": "hitting",
        "season": season,
        "sitCodes": sit_code,
    }

    return get_json(url, params)
