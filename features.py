from datetime import datetime, timedelta
from config import ET
from stats import get_pitcher_stats, get_pitcher_game_log, get_recent_games, get_team_stats, get_team_pitching_stats
from utils import parse_ip
CURRENT_SEASON = datetime.now(ET).year

def safe_float(value, default):
    try:
        if value in [None, "", "-.--"]: return default
        return float(value)
    except Exception:
        return default

def calculate_recent_form(team_id, days=21, max_games=10):
    end=datetime.now(ET).date(); start=end-timedelta(days=days)
    games=get_recent_games(team_id, start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))
    completed=[]
    for day in games.get("dates",[]):
        for game in day.get("games",[]):
            if game.get("status",{}).get("detailedState") == "Final": completed.append(game)
    completed=completed[-max_games:]
    wins=losses=runs_scored=runs_allowed=0
    for game in completed:
        home=game["teams"]["home"]; away=game["teams"]["away"]
        if home["team"]["id"] == team_id:
            scored=int(home.get("score",0)); allowed=int(away.get("score",0))
        else:
            scored=int(away.get("score",0)); allowed=int(home.get("score",0))
        runs_scored += scored; runs_allowed += allowed
        if scored > allowed: wins += 1
        else: losses += 1
    games_played=max(1,wins+losses)
    return {"wins_last10":wins,"losses_last10":losses,"recent_games":wins+losses,"win_pct":round(wins/games_played,3),"runs_per_game":round(runs_scored/games_played,2),"runs_allowed":round(runs_allowed/games_played,2),"run_diff":round((runs_scored-runs_allowed)/games_played,2)}

def pitcher_rating(p):
    era=safe_float(p.get("era"),4.50); whip=safe_float(p.get("whip"),1.35); k9=safe_float(p.get("k9"),8.0); bb9=safe_float(p.get("bb9"),3.2)
    last5_era=safe_float(p.get("last5_era"),era); last5_whip=safe_float(p.get("last5_whip"),whip)
    rating=50
    rating += (4.50-era)*8 + (1.35-whip)*25 + (k9-8.0)*3 + (3.2-bb9)*4 + (4.50-last5_era)*4 + (1.35-last5_whip)*12
    return round(max(20,min(100,rating)),1)

def default_pitcher_features():
    f={"era":4.50,"whip":1.35,"k9":8.0,"bb9":3.2,"last5_era":4.50,"last5_whip":1.35}
    f["rating"] = pitcher_rating(f)
    return f

def pitcher_last5(player_id, fallback_era, fallback_whip):
    try:
        logs=get_pitcher_game_log(player_id, CURRENT_SEASON); splits=logs["stats"][0].get("splits",[])[:5]
        innings=earned_runs=walks_hits=0.0
        for game in splits:
            stat=game.get("stat",{}); ip=parse_ip(stat.get("inningsPitched",0))
            earned_runs += safe_float(stat.get("earnedRuns"),0); walks_hits += safe_float(stat.get("hits"),0)+safe_float(stat.get("baseOnBalls"),0); innings += ip
        if innings > 0: return (earned_runs*9)/innings, walks_hits/innings
    except Exception: pass
    return fallback_era, fallback_whip

def pitcher_features(player_id):
    if not player_id: return default_pitcher_features()
    try:
        stats=get_pitcher_stats(player_id, CURRENT_SEASON); split=stats["stats"][0]["splits"][0]["stat"]
        era=safe_float(split.get("era"),4.50); whip=safe_float(split.get("whip"),1.35); k9=safe_float(split.get("strikeoutsPer9Inn"),8.0); bb9=safe_float(split.get("walksPer9Inn"),3.2)
    except Exception:
        era=4.50; whip=1.35; k9=8.0; bb9=3.2
    last5_era,last5_whip=pitcher_last5(player_id, era, whip)
    f={"era":era,"whip":whip,"k9":k9,"bb9":bb9,"last5_era":round(last5_era,2),"last5_whip":round(last5_whip,2)}
    f["rating"] = pitcher_rating(f)
    return f

def season_team_stats(team_id):
    try:
        stats=get_team_stats(team_id, CURRENT_SEASON); split=stats["stats"][0]["splits"][0]["stat"]
        return {"runs":safe_float(split.get("runs"),0),"hits":safe_float(split.get("hits"),0),"ops":safe_float(split.get("ops"),0.700),"avg":safe_float(split.get("avg"),0.240),"obp":safe_float(split.get("obp"),0.310),"slg":safe_float(split.get("slg"),0.390)}
    except Exception:
        return {"runs":0,"hits":0,"ops":0.700,"avg":0.240,"obp":0.310,"slg":0.390}

def bullpen_rating(era, whip, usage):
    rating=50 + (4.20-era)*10 + (1.35-whip)*30 - usage*1.5
    return round(max(20,min(100,rating)),1)

def bullpen_usage_last3(team_id):
    end=datetime.now(ET).date(); start=end-timedelta(days=3)
    try:
        games=get_recent_games(team_id, start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"))
        usage=0
        for day in games.get("dates",[]):
            for game in day.get("games",[]):
                if game.get("status",{}).get("detailedState") == "Final": usage += 1
        return usage
    except Exception:
        return 0

def bullpen_features(team_id):
    try:
        stats=get_team_pitching_stats(team_id, CURRENT_SEASON); split=stats["stats"][0]["splits"][0]["stat"]
        era=safe_float(split.get("era"),4.20); whip=safe_float(split.get("whip"),1.35)
    except Exception:
        era=4.20; whip=1.35
    usage=bullpen_usage_last3(team_id)
    return {"bullpen_era":era,"bullpen_whip":whip,"bullpen_usage":usage,"rating":bullpen_rating(era,whip,usage)}

home_pitcher_hand = get_pitcher_hand(game.get("home_pitcher_id"))
away_pitcher_hand = get_pitcher_hand(game.get("away_pitcher_id"))

home_offense = offense_features(home_id, away_pitcher_hand)
away_offense = offense_features(away_id, home_pitcher_hand)


def build_features(schedule):
    features=[]
    for game in schedule:
        home_id=game["home_id"]; away_id=game["away_id"]
        features.append({"home":game["home"],"away":game["away"],"home_form":calculate_recent_form(home_id),"away_form":calculate_recent_form(away_id),"home_pitcher":pitcher_features(game.get("home_pitcher_id")),"away_pitcher":pitcher_features(game.get("away_pitcher_id")),"home_team":season_team_stats(home_id),"away_team":season_team_stats(away_id),"home_bullpen":bullpen_features(home_id),"away_bullpen":bullpen_features(away_id),"market":game.get("market",{})})
    return features
    
from stats import get_team_hitting_splits, get_player

def get_pitcher_hand(player_id):
    if not player_id:
        return "R"

    try:
        data = get_player(player_id)
        person = data["people"][0]
        return person.get("pitchHand", {}).get("code", "R")
    except Exception:
        return "R"


def offense_rating_from_ops(ops):
    rating = 50
    rating += (ops - 0.700) * 120
    return round(max(20, min(100, rating)), 1)


def offense_features(team_id, opposing_pitcher_hand):
    try:
        stats = get_team_hitting_splits(
            team_id,
            CURRENT_SEASON,
            opposing_pitcher_hand,
        )

        split = stats["stats"][0]["splits"][0]["stat"]

        ops = safe_float(split.get("ops"), 0.700)
        avg = safe_float(split.get("avg"), 0.240)
        obp = safe_float(split.get("obp"), 0.310)
        slg = safe_float(split.get("slg"), 0.390)

    except Exception:
        ops = 0.700
        avg = 0.240
        obp = 0.310
        slg = 0.390

    return {
        "ops_vs_hand": ops,
        "avg_vs_hand": avg,
        "obp_vs_hand": obp,
        "slg_vs_hand": slg,
        "opposing_pitcher_hand": opposing_pitcher_hand,
        "rating": offense_rating_from_ops(ops),
    }
