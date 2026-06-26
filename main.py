import os, json, requests
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

APPS_SCRIPT_URL = os.environ["APPS_SCRIPT_URL"]
APPS_SCRIPT_TOKEN = os.environ["APPS_SCRIPT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def get_today_games():
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
    data = requests.get(url, timeout=20).json()

    games = []
    for date in data.get("dates", []):
        for game in date.get("games", []):
            away = game["teams"]["away"]["team"]["name"]
            home = game["teams"]["home"]["team"]["name"]
            games.append(f"{away} @ {home}")
    return today, games

def generate_picks():
    today, games = get_today_games()
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Today is {today}. These are the ONLY MLB games available today:

{json.dumps(games, indent=2)}

Generate exactly 5 MLB betting picks.

Rules:
- Pick ONLY from the listed games.
- No player props.
- Only Moneyline, Run Line, or Total.
- Mark exactly one as best_bet true.
- Confidence must be 1 to 5.
- Do not invent sportsbook odds.
- Leave odds blank if unavailable.
- Return ONLY a raw JSON array.

Fields:
date, game, pick, bet_type, odds, confidence, stake_units, result, profit_loss, notes
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    text = response.output_text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)

def main():
    picks = generate_picks()

    res = requests.post(
        APPS_SCRIPT_URL,
        json={"token": APPS_SCRIPT_TOKEN, "picks": picks},
        timeout=30
    )

    print(res.status_code)
    print(res.text)

    if "Success" not in res.text:
        raise RuntimeError("Apps Script did not return Success")

if __name__ == "__main__":
    main()
