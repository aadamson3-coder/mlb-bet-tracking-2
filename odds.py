import requests
import os

ODDS_API_KEY = os.environ["ODDS_API_KEY"]

BASE_URL = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

BOOKMAKERS = [
    "draftkings",
    "betmgm",
    "fanatics"
]

MARKETS = [
    "h2h",
    "spreads",
    "totals"
]


def get_odds():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": ",".join(MARKETS),
        "oddsFormat": "american",
        "bookmakers": ",".join(BOOKMAKERS)
    }

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def normalize_game_key(away, home):
    return f"{away} @ {home}"


def get_best_price_for_outcome(bookmakers, market_key, outcome_name, point=None):
    best = None

    for book in bookmakers:
        book_name = book.get("title", book.get("key", ""))

        for market in book.get("markets", []):
            if market.get("key") != market_key:
                continue

            for outcome in market.get("outcomes", []):
                if outcome.get("name") != outcome_name:
                    continue

                if point is not None and outcome.get("point") != point:
                    continue

                price = outcome.get("price")
                if price is None:
                    continue

                if best is None or price > best["odds"]:
                    best = {
                        "book": book_name,
                        "odds": price,
                        "point": outcome.get("point")
                    }

    return best


def build_market_map():
    raw_events = get_odds()
    markets = {}

    for event in raw_events:
        away = event["away_team"]
        home = event["home_team"]
        game_key = normalize_game_key(away, home)

        bookmakers = event.get("bookmakers", [])

        markets[game_key] = {
            "home": home,
            "away": away,
            "moneyline": {
                "home": get_best_price_for_outcome(bookmakers, "h2h", home),
                "away": get_best_price_for_outcome(bookmakers, "h2h", away)
            },
            "run_line": {
                "home": None,
                "away": None
            },
            "totals": {
                "over": None,
                "under": None
            }
        }

        # Spreads
        spread_points = set()

        for book in bookmakers:
            for market in book.get("markets", []):
                if market.get("key") == "spreads":
                    for outcome in market.get("outcomes", []):
                        spread_points.add(outcome.get("point"))

        for point in spread_points:
            home_rl = get_best_price_for_outcome(bookmakers, "spreads", home, point)
            away_rl = get_best_price_for_outcome(bookmakers, "spreads", away, -point if point is not None else None)

            if home_rl:
                markets[game_key]["run_line"]["home"] = home_rl

            if away_rl:
                markets[game_key]["run_line"]["away"] = away_rl

        # Totals
        total_points = set()

        for book in bookmakers:
            for market in book.get("markets", []):
                if market.get("key") == "totals":
                    for outcome in market.get("outcomes", []):
                        total_points.add(outcome.get("point"))

        for point in total_points:
            over = get_best_price_for_outcome(bookmakers, "totals", "Over", point)
            under = get_best_price_for_outcome(bookmakers, "totals", "Under", point)

            if over:
                markets[game_key]["totals"]["over"] = over

            if under:
                markets[game_key]["totals"]["under"] = under

    return markets
