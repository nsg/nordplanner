import time
import datetime
import os
import json

import mqtt
import nordpool
import yr

#
# Read config from options.json and the environment
#
config = json.load(open("/data/options.json"))
mqtt_host = os.environ["MQTT_HOST"]
mqtt_topic = config["mqtt_topic"]
mqtt_username = os.environ["MQTT_USERNAME"]
mqtt_password = os.environ["MQTT_PASSWORD"]
long = config["yr_location_longitude"]
lat = config["yr_location_latitude"]
house_temperature = config["default_house_temperature"]
temp_increase_constant = config["temp_increase_constant"]
temp_decrease_constant = config["temp_decrease_constant"]

today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)

schedule = {}


def get_temp_decrease_value(outside_temp, inside_temp):
    return round((inside_temp - outside_temp) / temp_decrease_constant, 2)


def get_temp_increase_value(outside_temp, inside_temp):
    return round((inside_temp - outside_temp) / temp_increase_constant, 2)


def schedule_updates(client, userdata, msg):
    global schedule

    topic_type = msg.topic.split("/")[-1]
    topic_hour = int(msg.topic.split("/")[-2])

    if not schedule.get(topic_hour):
        schedule[topic_hour] = {}

    if topic_type == "data":
        payload = json.loads(msg.payload.decode())
        schedule[topic_hour]["target"] = payload["target"]
        schedule[topic_hour]["override"] = payload.get("override", False)
    elif topic_type == "status":
        payload = msg.payload.decode()
        target = schedule[topic_hour].get("target", 0)
        override = schedule[topic_hour].get("override", False)
        schedule[topic_hour]["status"] = payload

        if payload == "online" and target >= 18:
            # User has manually enabled an offline hour
            target = schedule[0].get("target", 5)
            print(
                f"Override target temperature for hour {topic_hour}, set to {target} degrees"
            )
            data = {"target": target, "override": True}
            mq.publish(f"plan/schedule/{topic_hour}/data", json.dumps(data))
        elif payload == "offline" and override:
            # User has disabled and overridden hour
            data = {"target": 20, "override": False}
            mq.publish(f"plan/schedule/{topic_hour}/data", json.dumps(data))


def update_house_temperature(client, userdata, msg):
    global house_temperature

    house_temperature = float(msg.payload.decode())


def refresh(client, userdata, msg):
    global schedule

    schedule = {}
    temperatures = yr.get_temperatures(long, lat)
    nordpool_data = nordpool.get_data_for_tomorrow()

    # Try a few different plans, use the best one!
    plan1 = plan_day(
        temperatures,
        nordpool_data,
        start_temp=house_temperature,
        cutoff_price=20,
        end_temp=22,
    )
    plan2 = plan_day(
        temperatures,
        nordpool_data,
        start_temp=house_temperature,
        cutoff_price=20,
        end_temp=23,
    )
    plan3 = plan_day(
        temperatures,
        nordpool_data,
        start_temp=house_temperature,
        cutoff_price=20,
        end_temp=23,
        min_temp=18,
    )

    # Base plan, use this unless we find something better
    plan = plan1

    # Will a little extra heat help?
    if plan2["max_price"] > plan1["max_price"]:
        print("Use plan2: Heath the house a little extra")
        plan = plan2

    # If it's expensive, accept a cooler minimum temperature
    if plan["max_price"] > 70 and plan3["max_price"] < plan["max_price"]:
        print("Use plan3: Expensive price, I will allow a colder minimum temperature")
        plan = plan3

    mq.publish("plan/max_price", plan["max_price"])

    i = 0
    for h in plan["hours"]:
        k = f"plan/schedule/{i}"
        jsn = {"target": h["target"]}
        if h["active"]:
            mq.publish(f"{k}/status", "online")
        else:
            mq.publish(f"{k}/status", "offline")

        mq.publish(f"{k}/data", json.dumps(jsn))
        time.sleep(0.2)
        i = i + 1
    mq.publish("plan/refreshed_at", cur_datetime())


def plan_day(
    temperatures, nordpool_data, cutoff_price, start_temp=20.4, end_temp=21, min_temp=19
):
    temp = start_temp
    cold = False
    ret = {"to_cold": False, "max_price": cutoff_price, "hours": [None] * 24}
    for hour in range(24):
        npd = nordpool_data[hour]
        wfd = temperatures[hour]
        fire = False

        if npd < cutoff_price:
            if temp < end_temp:
                temp = temp + get_temp_increase_value(wfd, temp)
                fire = True

        tmp_dec_value = get_temp_decrease_value(wfd, temp)
        temp = temp - tmp_dec_value
        if temp < min_temp:
            cold = True

        ret["hours"][hour] = {
            "target": 20,
            "price": npd,
            "active": fire,
            "indoor_forecast": f"{temp:.1f}",
            "outdoor_forecast": wfd,
            "lost_temperature": tmp_dec_value,
        }

        if fire:
            ret["hours"][hour]["target"] = round(wfd)

    if cold:
        return plan_day(
            temperatures,
            nordpool_data,
            cutoff_price + 1,
            start_temp,
            end_temp,
            min_temp,
        )
    else:
        return ret


def cur_datetime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#
# Connect to MQTT and subscribe to topics
#
mq = mqtt.MQTT(mqtt_host, mqtt_topic, mqtt_username, mqtt_password)
mq.subscribe("plan/refresh", refresh)
mq.subscribe("plan/schedule/#", schedule_updates)
mq.subscribe("house_temperature", update_house_temperature)

while True:
    hour = int(datetime.datetime.today().hour)
    minute = int(datetime.datetime.today().minute)

    #
    # One ever hour, look at the hours data and trigger an update
    #
    if minute == 0:
        hourly_schedule = schedule.get(hour)
        if hourly_schedule:
            target = hourly_schedule["target"]
            print(f"Temperature set to {target}")
            mq.publish("set_temperature", target)
    time.sleep(30)
