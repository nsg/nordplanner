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


def set_target_temperature(hour, value):
    target = {"target_temperature": value}
    data = {**schedule[hour], **target}
    mq.publish(f"plan/schedule/{hour}/data", json.dumps(data))


def get_off_temperature(hour):
    global schedule

    if schedule[hour]["outside_temperature"] < 5:
        # Do not disable heat pump completly if there is below freezing outside
        # to protect the water. I'm not fully sure if the cirulation pump is stopped
        # or so I play safe.
        return SUMMER_MODE_TEMPERATURE - 4
    else:
        return SUMMER_MODE_TEMPERATURE


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

            # TODO: Read this from MQTT, and add it as helpers in HA
            cheap_power_cutoff_value = 100
            house_min_temperature_value = 18
            house_max_temperature_value = 21.5

            if house_temperature < house_min_temperature_value:
                # It's to cold inside, set real temperature (allow use of electric cartage)
                set_target_temperature(
                    current_hour, schedule[current_hour]["outside_temperature"]
                )
            if house_temperature > house_max_temperature_value:
                set_target_temperature(current_hour, get_off_temperature(current_hour))
            elif schedule[current_hour]["nordpool_data"] < cheap_power_cutoff_value:
                # It's cheap power, set real temperature (allow use of electric cartage)
                set_target_temperature(
                    current_hour, schedule[current_hour]["outside_temperature"]
                )
            else:
                # Set a fake temparature, heat pump only
                set_target_temperature(current_hour, 6)

            if schedule[current_hour]['status'] == 'online':
                # Enable it an 1.5 hours before the selected start time
                schedule48[last_hour * 2 - 1] = schedule[last_2hour][
                    "target_temperature"
                ]
                schedule48[last_hour * 2] = schedule[last_hour]["target_temperature"]
                schedule48[last_hour * 2 + 1] = schedule[last_hour][
                    "target_temperature"
                ]

                # Also enable it for the selected time
                schedule48[current_hour * 2] = schedule[current_hour][
                    "target_temperature"
                ]
                schedule48[current_hour * 2 + 1] = schedule[current_hour][
                    "target_temperature"
                ]
            else:
                # Enable summer mode a hour before the selected time
                schedule48[last_hour * 2] = get_off_temperature(last_hour)
                schedule48[last_hour * 2 + 1] = get_off_temperature(last_hour)

                # Also enable it for the selected time
                schedule48[current_hour * 2] = get_off_temperature(current_hour)
                schedule48[current_hour * 2 + 1] = get_off_temperature(current_hour)

        # for k, v in schedule48.items():
        #     print(f"{k} ({k/2}) \t {v} \t {schedule[int(k/2)]['status']} {schedule[int(k/2)]['target_temperature']}", flush=True)
        # print("", flush=True)


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
