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
        # Data has updated, update the local state
        payload = json.loads(msg.payload.decode())
        schedule[topic_hour] = {**schedule[topic_hour], **payload}

    elif topic_type == "status":
        # Status has changed, possible trigger logic!

        status = { "status": msg.payload.decode() }
        schedule[topic_hour] = {**schedule[topic_hour], **status}

        #target = schedule[topic_hour].get("target_temperature", 0)

        #if payload == "online":
        #    mq.publish(f"plan/schedule/{topic_hour}/data", json.dumps(schedule[topic_hour]))
        #elif payload == "offline" and override:
        #    # User has disabled and overridden hour
        #    data = {"target": 20, "override": False}
        #    mq.publish(f"plan/schedule/{topic_hour}/data", json.dumps(data))


def update_house_temperature(client, userdata, msg):
    global house_temperature

    house_temperature = float(msg.payload.decode())


def refresh(client, userdata, msg):

    temperatures = yr.get_temperatures(long, lat)
    nordpool_data = nordpool.get_data_for_tomorrow()

    for h in range(24):
        topic_path = f"plan/schedule/{h}"
        json_data = {
            "outside_temperature": temperatures[h],
            "nordpool_data": nordpool_data[h],
            "target_temperature": 6
        }
        mq.publish(f"{topic_path}/status", "online")
        mq.publish(f"{topic_path}/data", json.dumps(json_data))
        time.sleep(0.2)
    mq.publish("plan/refreshed_at", cur_datetime())


def cur_datetime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_top_of_hour():
    minute = int(datetime.datetime.today().minute)
    return minute == 0


#
# Connect to MQTT and subscribe to topics
#
mq = mqtt.MQTT(mqtt_host, mqtt_topic, mqtt_username, mqtt_password)
mq.subscribe("plan/refresh", refresh)
mq.subscribe("plan/schedule/#", schedule_updates)
mq.subscribe("house_temperature", update_house_temperature)

while True:
    hour = int(datetime.datetime.today().hour)

    if is_top_of_hour():
        hourly_schedule = schedule.get(hour)
        if hourly_schedule:
            target = hourly_schedule["target_temperature"]
            print(f"Temperature set to {target}")
            mq.publish("set_temperature", target)
    time.sleep(30)
