import requests
from config import ODDS_API_KEY, BOOKS, MARKETS

def get_odds():
    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": MARKETS,
        "oddsFormat": "american",
        "bookmakers": ",".join(BOOKS),
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()
