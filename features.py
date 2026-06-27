from datetime import datetime

from stats import (
    get_pitcher_stats,
    get_pitcher_game_log,
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
    if not player_id:
        return {
            "era": 4.50,
            "whip": 1.35,
            "k9": 8.0,
            "bb9": 3.2,
            "last5_era": 4.50,
            "last5_whip": 1.35,
        }

    stats = get_pitcher_stats(player_id, CURRENT_SEASON)

    try:
        split = stats["stats"][0]["splits"][0]["stat"]

        era = float(split.get("era", 4.50))
        whip = float(split.get("whip", 1.35))
        k9 = float(split.get("strikeoutsPer9Inn", 8.0))
        bb9 = float(split.get("walksPer9Inn", 3.2))

    except Exception:
        era = 4.50
        whip = 1.35
        k9 = 8.0
        bb9 = 3.2

    # Last 5 starts / appearances
    try:
        from stats import get_pitcher_game_log

        logs = get_pitcher_game_log(player_id, CURRENT_SEASON)
        splits = logs["stats"][0]["splits"][:5]

        innings = 0
        earned_runs = 0
        walks_hits = 0

        for game in splits:
            stat = game["stat"]

            ip = float(stat.get("inningsPitched", 0).replace(".1", ".333").replace(".2", ".667"))
            er = float(stat.get("earnedRuns", 0))
            hits = float(stat.get("hits", 0))
            walks = float(stat.get("baseOnBalls", 0))

            innings += ip
            earned_runs += er
            walks_hits += hits + walks

        if innings > 0:
            last5_era = (earned_runs * 9) / innings
            last5_whip = walks_hits / innings
        else:
            last5_era = era
            last5_whip = whip

    except Exception:
        last5_era = era
        last5_whip = whip

    return {
        "era": era,
        "whip": whip,
        "k9": k9,
        "bb9": bb9,
        "last5_era": round(last5_era, 2),
        "last5_whip": round(last5_whip, 2),
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
