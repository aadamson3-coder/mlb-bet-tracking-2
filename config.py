import os
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL")
APPS_SCRIPT_TOKEN = os.getenv("APPS_SCRIPT_TOKEN")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

BOOKMAKERS = ["draftkings", "betmgm", "fanatics"]
MARKETS = ["h2h", "spreads", "totals"]

MODEL_WEIGHTS = {
    "pitching": 0.30,
    "offense": 0.18,
    "team_form": 0.14,
    "bullpen": 0.20,
    "home_field": 0.05,
    "market": 0.13,
}

DEFAULT_UNIT_SIZE = 1.0
MAX_KELLY_UNITS = 3.0
FRACTIONAL_KELLY = 0.25
