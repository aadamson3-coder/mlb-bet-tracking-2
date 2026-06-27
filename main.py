import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

APPS_SCRIPT_URL = os.environ["APPS_SCRIPT_URL"]
APPS_SCRIPT_TOKEN = os.environ["APPS_SCRIPT_TOKEN"]
ODDS_API_KEY = os.environ["ODDS_API_KEY"]

ET = ZoneInfo("America/New_York")
BOOKS = ["draftkings", "betmgm", "fanduel", "fanatics"]
MARKETS = "h2h,spreads,totals"


def today_et():
    return datetime.now(ET).strftime("%Y-%m-%d")


def american_to_implied(odds):
    odds = int(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def clamp(value, low, high):
    return max(low, min(high, value))


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
            }
    return schedule


def get_records():
    url = "https://statsapi.mlb.com/api/v1/standings"
    params = {"leagueId": "103,104", "season": datetime.now(ET).year}
    data = get_json(url, params=params)
    records = {}

    for group in data.get("records", []):
        for team_record in group.get("teamRecords", []):
            team = team_record["team"]["name"]
            wins = int(team_record.get("wins", 0))
            losses = int(team_record.get("losses", 0))
            games = max(1, wins + losses)
            records[team] = wins / games
    return records


def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": MARKETS,
        "oddsFormat": "american",
        "bookmakers": ",".join(BOOKS),
    }
    return get_json(url, params=params)


def build_candidates(events, schedule, records):
    candidates = []

    for event in events:
        game = f'{event["away_team"]} @ {event["home_team"]}'
        if game not in schedule:
            continue

        info = schedule[game]
        away = info["away"]
        home = info["home"]

        for bookmaker in event.get("bookmakers", []):
            book = bookmaker.get("title", bookmaker.get("key", ""))

            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                if market_key not in ["h2h", "spreads", "totals"]:
                    continue

                for outcome in market.get("outcomes", []):
                    odds = outcome.get("price")
                    if odds is None:
                        continue

                    implied = american_to_implied(odds)
                    adjustment = 0.0

                    bet_type = {"h2h": "Moneyline", "spreads": "Run Line", "totals": "Total"}[market_key]

                    if market_key in ["h2h", "spreads"]:
                        side = outcome["name"]
                        opponent = home if side == away else away
                        adjustment += (records.get(side, 0.500) - records.get(opponent, 0.500)) * 0.10
                        if side == home:
                            adjustment += 0.012
                    else:
                        adjustment += 0.005

                    model_prob = clamp(implied + adjustment, 0.40, 0.64)
                    edge = model_prob - implied
                    confidence = round(clamp(2.5 + edge * 55, 1, 5), 1)

                    point = outcome.get("point")
                    if market_key == "h2h":
                        pick = outcome["name"]
                    else:
                        pick = f'{outcome["name"]} {point}'.strip()

                    rationale = (
                        f"Live {book} line. Deterministic v1 edge model using market price, "
                        f"team record differential, home-field signal, and listed probables: "
                        f'{info["away_pitcher"]} vs {info["home_pitcher"]}.'
                    )

                    candidates.append({
                        "date": today_et(),
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
                        "rationale": rationale,
                    })

    return sorted(candidates, key=lambda x: (x["edge"], x["confidence"]), reverse=True)


def choose_picks(candidates):
    picks = []
    used_games = set()

    for candidate in candidates:
        if candidate["game"] in used_games:
            continue
        picks.append(candidate)
        used_games.add(candidate["game"])
        if len(picks) == 5:
            break

    if len(picks) < 5:
        raise RuntimeError(f"Only found {len(picks)} picks.")

    picks[0]["best_bet"] = True
    picks[0]["rationale"] = "Best Bet: highest deterministic model edge. " + picks[0]["rationale"]
    return picks


def post_to_sheet(picks):
    response = requests.post(
        APPS_SCRIPT_URL,
        json={"token": APPS_SCRIPT_TOKEN, "picks": picks},
        timeout=30,
    )
    print(response.status_code)
    print(response.text)
    if "Success" not in response.text:
        raise RuntimeError("Apps Script did not return Success")


def main():
    schedule = get_schedule()
    records = get_records()
    odds = get_odds()
    candidates = build_candidates(odds, schedule, records)
    picks = choose_picks(candidates)
    post_to_sheet(picks)


if __name__ == "__main__":
    main()
