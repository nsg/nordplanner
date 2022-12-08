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
schedule48 = {}

SUMMER_MODE_TEMPERATURE = 20


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


def regen_schedule48():
    global schedule
    global schedule48

    # My Elomax 250 will enable "summer mode" when:
    #   temperature > 18 for 60 minutes
    # It will be disabled when:
    #   temperature <= 15 for 90 minutes
    #
    # A temparature below 5 will use the power hungry (but quick) electric cartage
    # The electric cartage will be exclusivly used if the outdoor temperature is
    # below -20

    if len(schedule) >= 23:
        for current_hour in range(24):
            last_hour = 0 if current_hour - 1 < 0 else current_hour - 1
            last_2hour = 0 if last_hour -1 < 0 else last_hour -1

            if house_temperature < 18:
                # It's to cold inside, allow use of electric cartage
                temperature_key = "outside_temperature"
            else:
                temperature_key = "target_temperature"

            if schedule[current_hour]['status'] == 'online':
                # Enable it an 1.5 hours before the selected start time
                schedule48[last_hour*2-1] = schedule[last_2hour][temperature_key]
                schedule48[last_hour*2] = schedule[last_hour][temperature_key]
                schedule48[last_hour*2+1] = schedule[last_hour][temperature_key]

                # Also enable it for the selected time
                schedule48[current_hour*2] = schedule[current_hour][temperature_key]
                schedule48[current_hour*2+1] = schedule[current_hour][temperature_key]
            else:
                # Enable summer mode a hour before the selected time
                schedule48[last_hour*2] = SUMMER_MODE_TEMPERATURE
                schedule48[last_hour*2+1] = SUMMER_MODE_TEMPERATURE

                # Also enable it for the selected time
                schedule48[current_hour*2] = SUMMER_MODE_TEMPERATURE
                schedule48[current_hour*2+1] = SUMMER_MODE_TEMPERATURE

        #for k, v in schedule48.items():
        #    print(f"{k} ({k/2}) \t {v} \t {schedule[int(k/2)]['status']}", flush=True)
        #print("", flush=True)

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


#
# Connect to MQTT and subscribe to topics
#
mq = mqtt.MQTT(mqtt_host, mqtt_topic, mqtt_username, mqtt_password)
mq.subscribe("plan/refresh", refresh)
mq.subscribe("plan/schedule/#", schedule_updates)
mq.subscribe("house_temperature", update_house_temperature)

while True:
    hour = int(datetime.datetime.today().hour)

    regen_schedule48()

    if int(datetime.datetime.today().minute) == 0:
        hourly_temperature = schedule48.get(hour*2)
        if hourly_temperature:
            mq.publish("set_temperature", hourly_temperature)
    elif int(datetime.datetime.today().minute) == 30:
        hourly_temperature = schedule48.get(hour*2+1)
        if hourly_temperature:
            mq.publish("set_temperature", hourly_temperature)

    time.sleep(30)
