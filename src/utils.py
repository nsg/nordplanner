def get_temp_decrease_value(outside_temp, inside_temp, constant):
    return round(inside_temp - (inside_temp - outside_temp) / constant, 2)


def get_temp_increase_value(outside_temp, inside_temp, inc, boost, dec):
    decr = get_temp_decrease_value(outside_temp, inside_temp, dec)
    incr = inc / (inside_temp - outside_temp)
    if outside_temp < 5:
        incr = incr + boost
    return round(decr + incr, 2)


def plan_day(yr, nordpool, cutoff, temp, max, min, config):
    increase_constant = config["temp_increase_constant"]
    increase_constant_boost = config["temp_increase_constant_boost"]
    decrease_constant = config["temp_decrease_constant"]
    hours = []

    for hour in range(24):
        npd = nordpool[hour]
        wfd = yr[hour]
        hd = {
            "target": 20,
            "price": npd,
            "active": False,
            "indoor_forecast": f"{temp:.1f}",
            "outdoor_forecast": wfd,
        }

        if npd < cutoff and temp < max:
            temp = get_temp_increase_value(
                wfd, temp, increase_constant, increase_constant_boost, decrease_constant
            )
            hd["target"] = int(wfd)
            hd["active"] = True
        elif temp < min:
            return plan_day(yr, nordpool, cutoff + 5, temp, max, min, config)
        else:
            temp = get_temp_decrease_value(wfd, temp, decrease_constant)

        hours.append(hd)

    ret = {"max_price": cutoff, "hours": hours}
    return ret
