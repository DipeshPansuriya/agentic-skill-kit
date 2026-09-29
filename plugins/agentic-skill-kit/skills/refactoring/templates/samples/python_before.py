# Sample (fake data): freight charge calculation BEFORE refactoring.
# Smells: long method, deep nesting, flag argument, magic numbers, duplicated code.


def calc_charge(awb, actual_kg, l, w, h, pcs, commodity, is_dg, cust_type, express):
    total = 0
    if actual_kg is not None and actual_kg > 0:
        if pcs is not None and pcs > 0:
            vol = (l * w * h) / 6000 * pcs
            if vol > actual_kg:
                chg = vol
            else:
                chg = actual_kg
            # round up to next half kilo
            if chg - int(chg) > 0:
                if chg - int(chg) <= 0.5:
                    chg = int(chg) + 0.5
                else:
                    chg = int(chg) + 1
            if commodity == "GEN":
                if chg < 45:
                    rate = 5.20
                elif chg < 100:
                    rate = 4.10
                elif chg < 300:
                    rate = 3.60
                elif chg < 500:
                    rate = 3.20
                else:
                    rate = 2.90
                total = chg * rate
            elif commodity == "PER":
                if chg < 45:
                    rate = 5.20 + 0.80
                elif chg < 100:
                    rate = 4.10 + 0.80
                elif chg < 300:
                    rate = 3.60 + 0.80
                elif chg < 500:
                    rate = 3.20 + 0.80
                else:
                    rate = 2.90 + 0.80
                total = chg * rate
            else:
                raise ValueError("unknown commodity " + str(commodity))
            if is_dg == True:
                total = total + 75.0
                total = total + total * 0.10
            if express == True:
                total = total * 1.25
            if cust_type == "KEY":
                total = total - total * 0.05
            if total < 50.0:
                total = 50.0
        else:
            raise ValueError("pieces must be positive")
    else:
        raise ValueError("weight must be positive")
    return round(total, 2)


def calc_charge_list(items):
    result = []
    for i in range(len(items)):
        it = items[i]
        r = calc_charge(it["awb"], it["kg"], it["l"], it["w"], it["h"], it["pcs"],
                        it["commodity"], it["dg"], it["cust"], it["express"])
        result.append(r)
    return result


def old_calc_v1(awb, kg):
    # unused since 2019
    return kg * 5.2
