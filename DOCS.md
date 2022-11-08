# Nordplanner

## Prerequisites

* This service requires a mqtt service, it will automatically pickup the needed credentials from Home Assistant.
* The Add-on [Ohmigon](https://github.com/nsg/ohmigon)

## Configure

`mqtt_topic`

Specify the topic that Ohmigon uses, this add-on will also write data to this topic under `${mqtt_topic}/plan`.

`yr_location_longitude` and `yr_location_latitude` is used to specify your location for the temperature forecasts.

`temp_increase_constant` specify the rate the heating system can increase the temperature with. This value will be used to calculate the rate with this formula: `(temperature - outdoor_temperature) / temp_increase_constant - heat_loss`.

`temp_decrease_constant` specify the rate the house loses heat. This value will be used to calculate the rate with this formula: `(temperature - outdoor_temperature) / temp_decrease_constant`.

`default_house_temperature` just a default value, I expect you to setup a integration to update `${mqtt_topic}/house_temperature` with a real fresh value.
