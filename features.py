import requests

# -------------------------------
# Recent Team Form
# -------------------------------

def calculate_recent_form(team):
    """
    Placeholder.
    Eventually pull:
      - Last 10 record
      - Runs scored/game
      - Runs allowed/game
      - Home/Road splits
    """

    return {
        "wins_last10": 5,
        "runs_per_game": 4.5,
        "runs_allowed": 4.2
    }


# -------------------------------
# Starting Pitcher
# -------------------------------

def pitcher_features(name):
    """
    Placeholder until Statcast/Baseball Savant integration.
    """

    return {
        "era": 3.75,
        "whip": 1.18,
        "k9": 9.4,
        "last5_era": 3.30
    }


# -------------------------------
# Bullpen
# -------------------------------

def bullpen_features(team):
    """
    Placeholder.
    """

    return {
        "bullpen_era": 3.85,
        "bullpen_usage": 1
    }


# -------------------------------
# Build Feature Set
# -------------------------------

def build_features(schedule, odds):

    features = []

    for game in schedule:

        home = game["home_team"]
        away = game["away_team"]

        home_form = calculate_recent_form(home)
        away_form = calculate_recent_form(away)

        home_pitcher = pitcher_features(
            game.get("home_pitcher", "")
        )

        away_pitcher = pitcher_features(
            game.get("away_pitcher", "")
        )

        home_pen = bullpen_features(home)
        away_pen = bullpen_features(away)

        market = odds.get(
            f"{away}@{home}",
            {}
        )

        features.append({

            "home": home,
            "away": away,

            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,

            "home_form": home_form,
            "away_form": away_form,

            "home_bullpen": home_pen,
            "away_bullpen": away_pen,

            "market": market

        })

    return features
