import requests
from datetime import datetime, timedelta
from config import APPS_SCRIPT_URL, APPS_SCRIPT_TOKEN, ET

BASE_URL = "https://statsapi.mlb.com/api/v1"


def yesterday_et():
    return (datetime.now(ET).date() - timedelta(days=1)).strftime("%Y-%m-%d")


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_final_scores(date):
    url = f"{BASE_URL}/schedule"

    params = {
        "sportId": 1,
        "date": date,
    }

    data = get_json(url, params)

    results = []

    for day in data.get("dates", []):
        for game in day.get("games", []):
            status = game.get("status", {}).get("detailedState", "")

            if status != "Final":
                continue

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            away_score = int(game["teams"]["away"].get("score", 0))
            home_score = int(game["teams"]["home"].get("score", 0))

            winner = home_team if home_score > away_score else away_team

            results.append({
                "date": date,
                "game": f"{away_team} @ {home_team}",
                "away_team": away_team,
                "home_team": home_team,
                "away_score": away_score,
                "home_score": home_score,
                "winner": winner,
                "margin": home_score - away_score,
                "total_runs": home_score + away_score,
            })

    return results


def post_results_to_sheet(date, results):
    payload = {
        "token": APPS_SCRIPT_TOKEN,
        "action": "grade_results",
        "date": date,
        "results": results,
    }

    response = requests.post(
        APPS_SCRIPT_URL,
        json=payload,
        timeout=30,
    )

    print(response.status_code)
    print(response.text)

    if "Success" not in response.text:
        raise RuntimeError("Apps Script did not return Success")


def main():
    date = yesterday_et()
    results = get_final_scores(date)

    if not results:
        print(f"No final MLB games found for {date}")
        return

    post_results_to_sheet(date, results)


if __name__ == "__main__":
    main()
