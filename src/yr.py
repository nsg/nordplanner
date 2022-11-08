import requests
import datetime

import xml.etree.ElementTree as ET


def get_temperatures(lat, long, altitude=1):
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/classic?altitude={altitude}&lat={lat}&lon={long}"
    resp = requests.get(url, headers={"User-Agent": "nordplanner/yr-forecast"})
    ret = []
    if resp.status_code == 200:
        root = ET.fromstring(resp.text)
        for time in root.findall("./product/time"):
            for temperature in time.findall("./location/temperature"):
                temp = temperature.get("value")
                time_from = datetime.datetime.strptime(
                    time.get("from"), "%Y-%m-%dT%H:%M:%SZ"
                )
                time_to = datetime.datetime.strptime(
                    time.get("to"), "%Y-%m-%dT%H:%M:%SZ"
                )

                tomorrow = datetime.date.today() + datetime.timedelta(days=1)
                if time_from.day == tomorrow.day:
                    ret.append(float(temp))

    return ret
