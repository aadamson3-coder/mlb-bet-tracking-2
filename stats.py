def get_team_stats(team_id, season):

    url = f"{BASE_URL}/teams/{team_id}/stats"

    params = {
        "stats": "season",
        "group": "hitting",
        "season": season
    }

    return get_json(url, params)
