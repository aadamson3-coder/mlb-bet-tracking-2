import os, requests
from datetime import datetime
from zoneinfo import ZoneInfo

APPS_SCRIPT_URL = os.environ["APPS_SCRIPT_URL"]
APPS_SCRIPT_TOKEN = os.environ["APPS_SCRIPT_TOKEN"]
ODDS_API_KEY = os.environ["ODDS_API_KEY"]

BOOKS = ["draftkings", "betmgm", "fanduel", "fanatics"]
REGIONS = "us"
MARKETS = "h2h,spreads,totals"

def american_to_implied(odds):
    odds = int(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)

def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": "american",
        "bookmakers": ",".join(BOOKS)
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def score_pick(event, market_key, outcome, book):
    odds = outcome.get("price")
    if odds is None:
        return None

    implied = american_to_implied(odds)

    # Deterministic placeholder model.
    # Phase 2 will replace this with pitcher/team/bullpen features.
    model_prob = max(0.40, min(0.62, implied + 0.035))
    edge = model_prob - implied

    confidence = round(2.5 + edge * 50, 1)
    confidence = max(1, min(5, confidence))

    home = event["home_team"]
    away = event["away_team"]
    game = f"{away} @ {home}"

    bet_type = {
        "h2h": "Moneyline",
        "spreads": "Run Line",
        "totals": "Total"
    }[market_key]

    pick = outcome["name"]
    if market_key == "spreads":
        pick = f'{outcome["name"]} {outcome.get("point", "")}'
    elif market_key == "totals":
        pick = f'{outcome["name"]} {outcome.get("point", "")}'

    return {
        "date": datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d"),
        "game": game,
        "pick": pick,
        "bet_type": bet_type,
        "sportsbook": book,
        "odds": odds,
        "model_probability": round(model_prob, 3),
        "implied_probability": round(implied, 3),
        "edge": round(edge, 3),
        "confidence": confidence,
        "best_bet": False,
        "rationale": f"Ranked by deterministic edge model using live market odds from {book}."
    }

def build_picks():
    events = get_odds()
    candidates = []

    for event in events:
        for bookmaker in event.get("bookmakers", []):
            book = bookmaker["key"]
            for market in bookmaker.get("markets", []):
                if market["key"] not in ["h2h", "spreads", "totals"]:
                    continue
                for outcome in market.get("outcomes", []):
                    scored = score_pick(event, market["key"], outcome, book)
                    if scored:
                        candidates.append(scored)

    candidates.sort(key=lambda x: x["edge"], reverse=True)

    picks = []
    used_games = set()

    for c in candidates:
        if c["game"] in used_games:
            continue
        picks.append(c)
        used_games.add(c["game"])
        if len(picks) == 5:
            break

    if picks:
        picks[0]["best_bet"] = True
        picks[0]["rationale"] = "Best Bet: highest model edge from today’s live odds board."

    return picks

def main():
    picks = build_picks()

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
