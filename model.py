from utils import (
    american_to_implied,
    expected_value,
    confidence_from_edge,
    clamp,
    today_et,
)


PITCHING_WEIGHT = 0.35
TEAM_FORM_WEIGHT = 0.25
BULLPEN_WEIGHT = 0.20
HOME_FIELD_WEIGHT = 0.05
MARKET_WEIGHT = 0.15


def safe_float(value, default):
    try:
        if value in [None, "", "-.--"]:
            return default
        return float(value)
    except Exception:
        return default


def score_pitching(home_pitcher, away_pitcher):
    home_rating = safe_float(home_pitcher.get("rating"), 50)
    away_rating = safe_float(away_pitcher.get("rating"), 50)

    rating_diff = home_rating - away_rating

    score = 0.50 + clamp(rating_diff * 0.003, -0.12, 0.12)

    return clamp(score, 0.32, 0.68)


def score_team_form(home_form, away_form):
    score = 0.50

    home_wins = safe_float(home_form.get("wins_last10"), 5)
    away_wins = safe_float(away_form.get("wins_last10"), 5)

    home_rpg = safe_float(home_form.get("runs_per_game"), 4.5)
    away_rpg = safe_float(away_form.get("runs_per_game"), 4.5)

    home_ra = safe_float(home_form.get("runs_allowed"), 4.5)
    away_ra = safe_float(away_form.get("runs_allowed"), 4.5)

    score += clamp((home_wins - away_wins) * 0.012, -0.06, 0.06)
    score += clamp((home_rpg - away_rpg) * 0.010, -0.04, 0.04)
    score += clamp((away_ra - home_ra) * 0.010, -0.04, 0.04)

    return clamp(score, 0.35, 0.65)


def score_bullpen(home_pen, away_pen):
    score = 0.50

    home_era = safe_float(home_pen.get("bullpen_era"), 3.90)
    away_era = safe_float(away_pen.get("bullpen_era"), 3.90)

    home_usage = safe_float(home_pen.get("bullpen_usage"), 1)
    away_usage = safe_float(away_pen.get("bullpen_usage"), 1)

    score += clamp((away_era - home_era) * 0.012, -0.04, 0.04)
    score += clamp((away_usage - home_usage) * 0.020, -0.04, 0.04)

    return clamp(score, 0.35, 0.65)


def home_team_probability(game):
    pitching = score_pitching(
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
        pitching * PITCHING_WEIGHT
        + form * TEAM_FORM_WEIGHT
        + bullpen * BULLPEN_WEIGHT
        + 0.53 * HOME_FIELD_WEIGHT
        + 0.50 * MARKET_WEIGHT
    )

    return clamp(probability, 0.35, 0.70)


def get_moneyline_market(game, side):
    market = game.get("market", {})
    moneyline = market.get("moneyline", {})

    if side == "home":
        return moneyline.get("home")

    if side == "away":
        return moneyline.get("away")

    return None


def build_moneyline_pick(game, side, probability):
    market = get_moneyline_market(game, side)

    if not market:
        return None

    odds = market.get("odds")
    book = market.get("book")

    if odds is None:
        return None

    implied = american_to_implied(odds)
    edge = probability - implied
    ev = expected_value(probability, odds)

    team = game["home"] if side == "home" else game["away"]

    opponent = game["away"] if side == "home" else game["home"]

    rationale = (
        f"Deterministic model using pitching, recent form, bullpen, "
        f"home field, and best available price. "
        f"Model sees {team} at {probability:.1%} vs market implied {implied:.1%}. "
        f"Best price found at {book}. Opponent: {opponent}."
    )

    return {
        "date": today_et(),
        "game": f'{game["away"]} @ {game["home"]}',
        "pick": team,
        "bet_type": "Moneyline",
        "sportsbook": book,
        "odds": odds,
        "model_probability": round(probability, 3),
        "implied_probability": round(implied, 3),
        "edge": round(edge, 3),
        "ev": round(ev, 3),
        "confidence": confidence_from_edge(edge),
        "best_bet": False,
        "rationale": rationale,
    }


def rank_picks(feature_set):
    picks = []

    for game in feature_set:
        market = game.get("market", {})

        if not market:
            continue

        home_prob = home_team_probability(game)
        away_prob = 1 - home_prob

        home_pick = build_moneyline_pick(
            game,
            "home",
            home_prob,
        )

        away_pick = build_moneyline_pick(
            game,
            "away",
            away_prob,
        )

        if home_pick:
            picks.append(home_pick)

        if away_pick:
            picks.append(away_pick)

    picks.sort(
        key=lambda x: (
            x["ev"],
            x["edge"],
            x["confidence"],
        ),
        reverse=True,
    )

    final_picks = []
    used_games = set()

    for pick in picks:
        if pick["game"] in used_games:
            continue

        if pick["ev"] <= 0:
            continue

        final_picks.append(pick)
        used_games.add(pick["game"])

        if len(final_picks) == 5:
            break

    if len(final_picks) < 5:
        for pick in picks:
            if pick["game"] in used_games:
                continue

            final_picks.append(pick)
            used_games.add(pick["game"])

            if len(final_picks) == 5:
                break

    if final_picks:
        final_picks[0]["best_bet"] = True
        final_picks[0]["rationale"] = (
            "Best Bet: highest EV from deterministic model. "
            + final_picks[0]["rationale"]
        )

    return final_picks
