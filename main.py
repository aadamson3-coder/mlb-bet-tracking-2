from mlb_schedule import get_schedule
from odds import build_market_map
from features import build_features
from model import rank_picks
from sheets import post_picks


def main():

    schedule = get_schedule()

    market_map = build_market_map()

    # Attach odds to each scheduled game
    for game in schedule:
        key = f"{game['away']} @ {game['home']}"
        game["market"] = market_map.get(key, {})

    features = build_features(schedule)

    picks = rank_picks(features)

    post_picks(picks)


if __name__ == "__main__":
    main()
