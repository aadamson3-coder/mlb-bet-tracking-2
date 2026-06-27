from utils import american_to_implied, expected_value, confidence_from_edge, clamp, today_et
from config import MODEL_WEIGHTS

def safe_float(value, default):
    try:
        if value in [None, "", "-.--"]: return default
        return float(value)
    except Exception: return default

def score_pitching(home_pitcher, away_pitcher):
    diff=safe_float(home_pitcher.get("rating"),50)-safe_float(away_pitcher.get("rating"),50)
    return clamp(0.50+clamp(diff*0.003,-0.12,0.12),0.32,0.68)

def score_team_form(home_form, away_form):
    score=0.50
    score += clamp((safe_float(home_form.get("wins_last10"),5)-safe_float(away_form.get("wins_last10"),5))*0.012,-0.06,0.06)
    score += clamp((safe_float(home_form.get("runs_per_game"),4.5)-safe_float(away_form.get("runs_per_game"),4.5))*0.010,-0.04,0.04)
    score += clamp((safe_float(away_form.get("runs_allowed"),4.5)-safe_float(home_form.get("runs_allowed"),4.5))*0.010,-0.04,0.04)
    return clamp(score,0.35,0.65)

def score_bullpen(home_pen, away_pen):
    diff=safe_float(home_pen.get("rating"),50)-safe_float(away_pen.get("rating"),50)
    return clamp(0.50+clamp(diff*0.003,-0.10,0.10),0.35,0.65)

def home_team_probability(game):
    pitching=score_pitching(game["home_pitcher"],game["away_pitcher"]); form=score_team_form(game["home_form"],game["away_form"]); bullpen=score_bullpen(game["home_bullpen"],game["away_bullpen"])
    probability=pitching*MODEL_WEIGHTS["pitching"] + form*MODEL_WEIGHTS["team_form"] + bullpen*MODEL_WEIGHTS["bullpen"] + 0.53*MODEL_WEIGHTS["home_field"] + 0.50*MODEL_WEIGHTS["market"]
    return clamp(probability,0.35,0.70)

def get_moneyline_market(game, side):
    moneyline=game.get("market",{}).get("moneyline",{})
    return moneyline.get(side)

def build_moneyline_pick(game, side, probability):
    market=get_moneyline_market(game,side)
    if not market: return None
    odds=market.get("odds"); book=market.get("book")
    if odds is None: return None
    implied=american_to_implied(odds); edge=probability-implied; ev=expected_value(probability,odds)
    team=game["home"] if side=="home" else game["away"]; opponent=game["away"] if side=="home" else game["home"]
    pitcher=game["home_pitcher"] if side=="home" else game["away_pitcher"]; opponent_pitcher=game["away_pitcher"] if side=="home" else game["home_pitcher"]
    rationale=f"Model sees {team} at {probability:.1%} vs market implied {implied:.1%}. Best price found at {book}. Pitching rating {safe_float(pitcher.get('rating'),50):.1f} vs {safe_float(opponent_pitcher.get('rating'),50):.1f}. Opponent: {opponent}."
    return {"date":today_et(),"game":f'{game["away"]} @ {game["home"]}',"pick":team,"bet_type":"Moneyline","sportsbook":book,"odds":odds,"model_probability":round(probability,3),"implied_probability":round(implied,3),"edge":round(edge,3),"ev":round(ev,3),"confidence":confidence_from_edge(edge),"best_bet":False,"rationale":rationale}

def rank_picks(feature_set):
    picks=[]
    for game in feature_set:
        if not game.get("market",{}): continue
        home_prob=home_team_probability(game); away_prob=1-home_prob
        for pick in [build_moneyline_pick(game,"home",home_prob), build_moneyline_pick(game,"away",away_prob)]:
            if pick: picks.append(pick)
    picks.sort(key=lambda x:(x["ev"],x["edge"],x["confidence"]), reverse=True)
    final=[]; used_games=set()
    for pick in picks:
        if pick["game"] in used_games or pick["ev"] <= 0: continue
        final.append(pick); used_games.add(pick["game"])
        if len(final)==5: break
    if len(final)<5:
        for pick in picks:
            if pick["game"] in used_games: continue
            final.append(pick); used_games.add(pick["game"])
            if len(final)==5: break
    if final:
        final[0]["best_bet"]=True; final[0]["rationale"]="Best Bet: highest EV from deterministic model. "+final[0]["rationale"]
    return final
