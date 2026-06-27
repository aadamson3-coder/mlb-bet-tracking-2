from utils import american_to_implied, expected_value, clamp, confidence_from_edge, today_et

def make_candidates(odds_events, schedule, records, recent_form):
    candidates = []

    for event in odds_events:
        game = f'{event["away_team"]} @ {event["home_team"]}'
        if game not in schedule:
            continue

        info = schedule[game]
        away = info["away"]
        home = info["home"]

        for bookmaker in event.get("bookmakers", []):
            sportsbook = bookmaker.get("title", bookmaker.get("key", ""))

            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                if market_key not in ["h2h", "spreads", "totals"]:
                    continue

                for outcome in market.get("outcomes", []):
                    odds = outcome.get("price")
                    if odds is None:
                        continue

                    bet_type = {"h2h": "Moneyline", "spreads": "Run Line", "totals": "Total"}[market_key]
                    point = outcome.get("point")
                    pick = outcome["name"] if market_key == "h2h" else f'{outcome["name"]} {point}'.strip()

                    model_probability, notes = model_probability_for_pick(
                        outcome=outcome,
                        market_key=market_key,
                        odds=odds,
                        away=away,
                        home=home,
                        records=records,
                        recent_form=recent_form,
                    )

                    implied = american_to_implied(odds)
                    edge = model_probability - implied
                    ev = expected_value(model_probability, odds)
                    confidence = confidence_from_edge(edge)

                    rationale = (
                        f"Deterministic v2 score. {sportsbook} line. "
                        f"Probables: {info['away_pitcher']} vs {info['home_pitcher']}. "
                        + " ".join(notes)
                    )

                    candidates.append({
                        "date": today_et(),
                        "game": game,
                        "pick": pick,
                        "bet_type": bet_type,
                        "sportsbook": sportsbook,
                        "odds": odds,
                        "model_probability": round(model_probability, 3),
                        "implied_probability": round(implied, 3),
                        "edge": round(edge, 3),
                        "ev": round(ev, 3),
                        "confidence": confidence,
                        "best_bet": False,
                        "rationale": rationale,
                    })

    return sorted(candidates, key=lambda x: (x["ev"], x["edge"], x["confidence"]), reverse=True)

def model_probability_for_pick(outcome, market_key, odds, away, home, records, recent_form):
    implied = american_to_implied(odds)
    adjustment = 0.0
    notes = []

    if market_key in ["h2h", "spreads"]:
        side = outcome["name"]
        opponent = home if side == away else away

        season_adj = (records.get(side, {}).get("win_pct", 0.500) - records.get(opponent, {}).get("win_pct", 0.500)) * 0.08
        recent_adj = (recent_form.get(side, {}).get("recent_win_pct", 0.500) - recent_form.get(opponent, {}).get("recent_win_pct", 0.500)) * 0.06
        side_rd = recent_form.get(side, {}).get("recent_run_diff_per_game", 0.0)
        opp_rd = recent_form.get(opponent, {}).get("recent_run_diff_per_game", 0.0)
        run_diff_adj = clamp((side_rd - opp_rd) * 0.006, -0.025, 0.025)

        adjustment += season_adj + recent_adj + run_diff_adj

        if side == home:
            adjustment += 0.012
            notes.append("Home-field boost applied.")

        notes.append(f"Season form adj {season_adj:+.3f}.")
        notes.append(f"Recent form adj {recent_adj:+.3f}.")
        notes.append(f"Run differential adj {run_diff_adj:+.3f}.")

        if market_key == "spreads":
            adjustment *= 0.75
            notes.append("Run-line volatility haircut applied.")

    elif market_key == "totals":
        adjustment += 0.004
        notes.append("Conservative totals adjustment applied.")

    return clamp(implied + adjustment, 0.38, 0.66), notes

def choose_top_picks(candidates, count=5):
    picks = []
    used_games = set()

    for candidate in candidates:
        if candidate["game"] in used_games:
            continue
        if candidate["ev"] <= 0:
            continue
        picks.append(candidate)
        used_games.add(candidate["game"])
        if len(picks) == count:
            break

    if len(picks) < count:
        for candidate in candidates:
            if candidate["game"] in used_games:
                continue
            picks.append(candidate)
            used_games.add(candidate["game"])
            if len(picks) == count:
                break

    if picks:
        picks[0]["best_bet"] = True
        picks[0]["rationale"] = "Best Bet: highest EV from deterministic v2 model. " + picks[0]["rationale"]

    return picks
