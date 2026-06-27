schedule = get_schedule()

games = build_features(schedule)

picks = score_games(games)

post_to_sheet(picks)
