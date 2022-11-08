import requests
import json


def get_data_for_tomorrow():
    url = f"https://www.nordpoolgroup.com/api/marketdata/page/29?currency=SEK"
    r = requests.get(url)

    data = json.loads(r.text)["data"]

    # Loop over the returned rows
    ret = []
    for row in data["Rows"]:
        for col in row["Columns"]:
            if col["Name"] == "SE3" and not row["IsExtraRow"]:
                price = col["Value"]
                price = price.replace(",", ".")
                price = price.replace(" ", "")
                price_kwh = float(price) / 1000
                price_ore_kwh = int(round(price_kwh, 2) * 100)
                ret.append(price_ore_kwh)

    return ret
