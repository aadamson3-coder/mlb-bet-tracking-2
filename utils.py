from datetime import datetime
from config import ET

def today_et():
    return datetime.now(ET).strftime("%Y-%m-%d")

def american_to_implied(odds):
    odds = int(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)

def expected_value(model_probability, american_odds):
    odds = int(american_odds)
    profit_per_unit = odds / 100 if odds > 0 else 100 / abs(odds)
    return (model_probability * profit_per_unit) - (1 - model_probability)

def clamp(value, low, high):
    return max(low, min(high, value))

def confidence_from_edge(edge):
    if edge >= 0.08:
        return 5.0
    if edge >= 0.06:
        return 4.5
    if edge >= 0.04:
        return 4.0
    if edge >= 0.025:
        return 3.5
    if edge >= 0.015:
        return 3.0
    if edge >= 0.005:
        return 2.5
    return 2.0
