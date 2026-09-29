# Sample (fake data): freight charge calculation AFTER refactoring (same behaviour).
# Steps: guard clauses, replace magic numbers, lookup table for weight breaks,
# decompose conditional, remove duplicated rate ladder, loop -> comprehension,
# remove dead code (old_calc_v1 had no callers). Public signatures unchanged.
import math

VOLUMETRIC_DIVISOR = 6000  # cm3 per kg
MIN_CHARGE = 50.0
DG_FEE, DG_RATE = 75.0, 0.10
EXPRESS_FACTOR = 1.25
KEY_ACCOUNT_DISCOUNT = 0.05
COMMODITY_SURCHARGE = {"GEN": 0.0, "PER": 0.80}  # added to the per-kg rate
WEIGHT_BREAKS = [(45, 5.20), (100, 4.10), (300, 3.60), (500, 3.20), (math.inf, 2.90)]  # (below kg, rate)


def _positive(value):
    return value is not None and value > 0


def _round_up_to_half_kg(kg):
    return math.ceil(kg * 2) / 2


def _base_rate(kg):
    return next(rate for below, rate in WEIGHT_BREAKS if kg < below)


def calc_charge(awb, actual_kg, l, w, h, pcs, commodity, is_dg, cust_type, express):
    if not _positive(actual_kg):
        raise ValueError("weight must be positive")
    if not _positive(pcs):
        raise ValueError("pieces must be positive")
    volumetric_kg = l * w * h / VOLUMETRIC_DIVISOR * pcs
    kg = _round_up_to_half_kg(max(volumetric_kg, actual_kg))
    if commodity not in COMMODITY_SURCHARGE:
        raise ValueError(f"unknown commodity {commodity}")

    total = kg * (_base_rate(kg) + COMMODITY_SURCHARGE[commodity])
    if is_dg == True:  # noqa: E712 - legacy callers pass 1/0; pinned by characterization test
        total += DG_FEE
        total += total * DG_RATE
    if express == True:  # noqa: E712 - same reason
        total *= EXPRESS_FACTOR
    if cust_type == "KEY":
        total -= total * KEY_ACCOUNT_DISCOUNT
    return round(max(total, MIN_CHARGE), 2)


def calc_charge_list(items):
    return [calc_charge(it["awb"], it["kg"], it["l"], it["w"], it["h"], it["pcs"],
                        it["commodity"], it["dg"], it["cust"], it["express"]) for it in items]
