# MLB Tracker Cleanup

Replace these files:

1. GitHub `main.py` -> `main.py`
2. GitHub `.github/workflows/daily.yml` -> `daily.yml`
3. GitHub `requirements.txt` -> `requirements.txt`
4. Apps Script `Code.gs` -> `apps_script_Code.gs`

Then redeploy Apps Script as a new web app version and run the GitHub Action.

This version removes OpenAI from the picking flow and uses:
- official MLB schedule
- The Odds API live MLB lines
- deterministic scoring
- clean Google Sheet columns
