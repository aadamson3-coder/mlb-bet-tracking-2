from datetime import datetime

from stats import (
    get_pitcher_stats,
    get_recent_games,
    get_team_stats,
)


CURRENT_SEASON = datetime.now().year


# -------------------------------------------------
# Team Recent Form
# -------------------------------------------------

def calculate_recent_form(team_id):

    games = get_recent_games(team_id)

    wins = 0
    losses = 0

    runs_scored = 0
    runs_allowed = 0

    for day in games.get("dates", []):

        for game in day.get("games", []):

            if game["status"]["detailedState"] != "Final":
                continue

            home = game["teams"]["home"]
            away = game["teams"]["away"]

            if home["team"]["id"] == team_id:

                scored = home["score"]
                allowed = away["score"]

            else:

                scored = away["score"]
                allowed = home["score"]

            runs_scored += scored
            runs_allowed += allowed

            if scored > allowed:
                wins += 1
            else:
                losses += 1

    games_played = max(1, wins + losses)

    return {

        "wins_last10": wins,

        "losses_last10": losses,

        "win_pct": round(wins / games_played, 3),

        "runs_per_game":
            round(runs_scored / games_played, 2),

        "runs_allowed":
            round(runs_allowed / games_played, 2),

        "run_diff":
            round(
                (runs_scored - runs_allowed)
                / games_played,
                2
            )

    }


# -------------------------------------------------
# Starting Pitcher
# -------------------------------------------------

def pitcher_features(player_id):

    stats = get_pitcher_stats(
        player_id,
        CURRENT_SEASON,
    )

    try:

        split = stats["stats"][0]["splits"][0]["stat"]

        return {

            "era":
                float(split.get("era", 4.50)),

            "whip":
                float(split.get("whip", 1.35)),

            "k9":
                float(split.get("strikeoutsPer9Inn", 8.0))

        }

    except:

        return {

            "era": 4.50,

            "whip": 1.35,

            "k9": 8.0

        }


# -------------------------------------------------
# Team Season Stats
# -------------------------------------------------

def season_team_stats(team_id):

    stats = get_team_stats(
        team_id,
        CURRENT_SEASON,
    )

    try:

        split = stats["stats"][0]["splits"][0]["stat"]

        return {

            "runs":

                float(split.get("runs", 0)),

            "hits":

                float(split.get("hits", 0)),

            "ops":

                float(split.get("ops", .700))

        }

    except:

        return {

            "runs": 0,

            "hits": 0,

            "ops": .700

        }


# -------------------------------------------------
# Bullpen
# -------------------------------------------------

def bullpen_features(team_id):

    """
    Placeholder.

    We'll replace this with
    bullpen usage over
    previous 3 days.
    """

    return {

        "bullpen_era": 3.90,

        "bullpen_usage": 1

    }


# -------------------------------------------------
# Feature Builder
# -------------------------------------------------

def build_features(schedule):

    features = []

    for game in schedule:

        home = game["home"]
        away = game["away"]

        home_id = game["home_id"]
        away_id = game["away_id"]

        features.append({

            "home": home,

            "away": away,

            "home_form":
                calculate_recent_form(home_id),

            "away_form":
                calculate_recent_form(away_id),

            "home_pitcher":
                pitcher_features(
                    game["home_pitcher_id"]
                ),

            "away_pitcher":
                pitcher_features(
                    game["away_pitcher_id"]
                ),

            "home_team":
                season_team_stats(home_id),

            "away_team":
                season_team_stats(away_id),

            "home_bullpen":
                bullpen_features(home_id),

            "away_bullpen":
                bullpen_features(away_id),

            "market":
                game["market"]

        })

    return features
