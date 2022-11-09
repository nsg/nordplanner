# Nordplanner

## Prerequisites

* This service requires a mqtt service, it will automatically pickup the needed credentials from Home Assistant.
* The Add-on [Ohmigon](https://github.com/nsg/ohmigon)

## Configure

`mqtt_topic`

Specify the topic that Ohmigon uses, this add-on will also write data to this topic under `${mqtt_topic}/plan`.

`yr_location_longitude` and `yr_location_latitude` is used to specify your location for the temperature forecasts.

`temp_min_temperature` and `temp_max_temperature` temperatures

`temp_increase_constant` specify the rate the heating system can increase the temperature with. Larger value is considered faster. `temp_increase_constant_boost` is added to the constant when the electrical cartridge fires.

`temp_decrease_constant` specify the rate the house loses heat. Smaller value is considered faster.

`default_house_temperature` just a default value, I expect you to setup an automation to update `${mqtt_topic}/house_temperature` with a real fresh value.
