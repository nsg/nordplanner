import time
import datetime
import os
import json


import mqtt
import nordpool
import yr
import utils

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
temp_min_temperature = config["temp_min_temperature"]
temp_max_temperature = config["temp_max_temperature"]
temp_increase_constant_boost = config["temp_increase_constant_boost"]
temp_decrease_constant = config["temp_decrease_constant"]

today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)

schedule = {}


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

    plan = utils.plan_day(
        temperatures,
        nordpool_data,
        1,
        house_temperature,
        temp_max_temperature,
        temp_min_temperature,
        config,
    )

    print(f"max_price: {plan['max_price']}", flush=True)
    mq.publish("plan/max_price", plan["max_price"])

    i = 0
    for h in plan["hours"]:
        print(h, flush=True)

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
