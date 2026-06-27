from utils import (
    american_to_implied,
    expected_value,
    confidence_from_edge,
    clamp,
    today_et,
)


# -----------------------------
# Model Weights
# -----------------------------

PITCHING_WEIGHT = 0.35
TEAM_FORM_WEIGHT = 0.25
BULLPEN_WEIGHT = 0.20
HOME_FIELD_WEIGHT = 0.05
MARKET_WEIGHT = 0.15


# -----------------------------
# Feature Scoring Helpers
# -----------------------------

def score_pitching(home_pitcher, away_pitcher):
    score = 0.50

    if home_pitcher["era"] < away_pitcher["era"]:
        score += 0.05

    if home_pitcher["whip"] < away_pitcher["whip"]:
        score += 0.04

    if home_pitcher["k9"] > away_pitcher["k9"]:
        score += 0.03

    return clamp(score, 0.35, 0.65)


def score_team_form(home_form, away_form):
    score = 0.50

    score += (home_form["wins_last10"] - away_form["wins_last10"]) * 0.01

    score += (
        home_form["runs_per_game"]
        - away_form["runs_per_game"]
    ) * 0.01

    return clamp(score, 0.35, 0.65)


def score_bullpen(home_pen, away_pen):
    score = 0.50

    if home_pen["bullpen_era"] < away_pen["bullpen_era"]:
        score += 0.03

    if home_pen["bullpen_usage"] < away_pen["bullpen_usage"]:
        score += 0.02

    return clamp(score, 0.35, 0.65)


# -----------------------------
# Overall Game Model
# -----------------------------

def calculate_model_probability(game):

    pitch = score_pitching(
        game["home_pitcher"],
        game["away_pitcher"],
    )

    form = score_team_form(
        game["home_form"],
        game["away_form"],
    )

    bullpen = score_bullpen(
        game["home_bullpen"],
        game["away_bullpen"],
    )

    probability = (
        pitch * PITCHING_WEIGHT
        + form * TEAM_FORM_WEIGHT
        + bullpen * BULLPEN_WEIGHT
        + 0.50 * HOME_FIELD_WEIGHT
        + 0.50 * MARKET_WEIGHT
    )

    return clamp(probability, 0.35, 0.70)


# -----------------------------
# Rank Every Bet
# -----------------------------

def rank_picks(feature_set):

    picks = []

    for game in feature_set:

        market = game["market"]

        if not market:
            continue

        implied = american_to_implied(
            market["home_odds"]
        )

        probability = calculate_model_probability(game)

        edge = probability - implied

        ev = expected_value(
            probability,
            market["home_odds"],
        )

        picks.append({

            "date": today_et(),

            "game": f'{game["away"]} @ {game["home"]}',

            "pick": game["home"],

            "bet_type": "Moneyline",

            "sportsbook": market["book"],

            "odds": market["home_odds"],

            "model_probability": round(probability, 3),

            "implied_probability": round(implied, 3),

            "edge": round(edge, 3),

            "ev": round(ev, 3),

            "confidence": confidence_from_edge(edge),

            "best_bet": False,

            "rationale": (
                "Deterministic model using "
                "pitching, team form, bullpen, "
                "home field and market value."
            ),

        })

    picks.sort(
        key=lambda x: (
            x["ev"],
            x["edge"],
        ),
        reverse=True,
    )

    if picks:
        picks[0]["best_bet"] = True

    return picks[:5]
