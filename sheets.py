import requests
from config import APPS_SCRIPT_URL, APPS_SCRIPT_TOKEN

def post_picks(picks):
    response = requests.post(
        APPS_SCRIPT_URL,
        json={"token": APPS_SCRIPT_TOKEN, "picks": picks},
        timeout=30,
    )
    print(response.status_code)
    print(response.text)
    if "Success" not in response.text:
        raise RuntimeError("Apps Script did not return Success")
