from mlb_schedule import get_schedule, get_team_records
from odds import get_odds
from features import recent_team_form
from model import make_candidates, choose_top_picks
from sheets import post_picks


def main():
    schedule = get_schedule()
    records = get_team_records()
    recent_form = recent_team_form(days=14)
    odds_events = get_odds()

    candidates = make_candidates(
        odds_events=odds_events,
        schedule=schedule,
        records=records,
        recent_form=recent_form,
    )

    picks = choose_top_picks(candidates, count=5)

    if len(picks) < 5:
        raise RuntimeError(f"Only found {len(picks)} picks.")

    post_picks(picks)


if __name__ == "__main__":
    main()
