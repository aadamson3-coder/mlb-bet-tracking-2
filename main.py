import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

APPS_SCRIPT_URL = os.environ["APPS_SCRIPT_URL"]
APPS_SCRIPT_TOKEN = os.environ["APPS_SCRIPT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def generate_picks():
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Generate exactly 5 MLB betting picks for {today}.

Rules:
- No player props.
- Only Moneyline, Run Line, or Total.
- Mark exactly one as best_bet true.
- Confidence must be 1 to 5.
- Do not invent sportsbook odds. Leave odds blank if unavailable.
- Return ONLY a raw JSON array.
- Do not include markdown or commentary.

Fields:
date, game, pick, bet_type, betmgm, draftkings, fanatics, polymarketus, kalshi, best_odds, best_source, confidence, best_bet, rationale
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
        json={
            "token": APPS_SCRIPT_TOKEN,
            "picks": picks
        },
        timeout=30
    )

    print(res.status_code)
    print(res.text)

    if "Success" not in res.text:
        raise RuntimeError("Apps Script did not return Success")

if __name__ == "__main__":
    main()
