import os
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL")
APPS_SCRIPT_TOKEN = os.getenv("APPS_SCRIPT_TOKEN")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

BOOK_PRIORITY = [
    "draftkings",
    "betmgm",
    "fanatics",
    "kalshi",
    "polymarketus",
]
