from datetime import datetime
from config import ET, DEFAULT_UNIT_SIZE, MAX_KELLY_UNITS, FRACTIONAL_KELLY

def today_et():
    return datetime.now(ET).strftime("%Y-%m-%d")

def american_to_implied(odds):
    odds = int(odds)
    return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

def probability_to_american(probability):
    probability = clamp(probability, 0.01, 0.99)
    if probability >= 0.5:
        return round(-100 * probability / (1 - probability))
    return round(100 * (1 - probability) / probability)

def expected_value(model_probability, american_odds):
    odds = int(american_odds)
    profit_per_unit = odds / 100 if odds > 0 else 100 / abs(odds)
    return (model_probability * profit_per_unit) - (1 - model_probability)

def decimal_profit_multiple(american_odds):
    odds = int(american_odds)
    return odds / 100 if odds > 0 else 100 / abs(odds)

def kelly_units(model_probability, american_odds):
    b = decimal_profit_multiple(american_odds)
    p = clamp(model_probability, 0.001, 0.999)
    q = 1 - p
    full_kelly = ((b * p) - q) / b
    if full_kelly <= 0:
        return 0.0
    units = full_kelly * FRACTIONAL_KELLY * 10 * DEFAULT_UNIT_SIZE
    return round(clamp(units, 0.0, MAX_KELLY_UNITS), 2)

def clv_from_odds(bet_odds, closing_odds):
    if closing_odds in [None, "", 0]:
        return ""
    return round(american_to_implied(closing_odds) - american_to_implied(bet_odds), 4)

def clamp(value, low, high):
    return max(low, min(high, value))

def confidence_from_edge(edge):
    if edge >= 0.08: return 5.0
    if edge >= 0.06: return 4.5
    if edge >= 0.04: return 4.0
    if edge >= 0.025: return 3.5
    if edge >= 0.015: return 3.0
    if edge >= 0.005: return 2.5
    return 2.0

def parse_ip(ip_value):
    if ip_value in [None, "", "-.--"]:
        return 0.0
    text = str(ip_value)
    if "." not in text:
        return float(text)
    whole, frac = text.split(".", 1)
    whole = float(whole or 0)
    if frac == "1": return whole + (1 / 3)
    if frac == "2": return whole + (2 / 3)
    try:
        return float(text)
    except Exception:
        return whole
