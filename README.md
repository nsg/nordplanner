# Nordplanner

![](/docs/screenshot-example-graph.png)

This is a plugin that I use together with the add-on [ohmigon](https://github.com/nsg/ohmigon) to control my heating system. I collect weather forecasts from Yr, electric prices from North Pool and then I do some number crunching to figure out when to heat my home.

The idea is to save money, we have hourly spot prices from our electricity provider. It will also have the added bonus of helping the current energy crises in Europe buy using energy when there is plenty. It will probably help the environment a little as well, the base load is usually green here in Sweden.

## Prerequisites

The add-on [Ohmigon](https://github.com/nsg/ohmigon) to control the heating system. State and communication with Ohmigon will be done over MQTT.

## The idea

Build up a thermal mass in the house, overheat it a little when it's cheap and let the temperature drop when the price is high. How well this works do depend on your heating solution, insulation and daily routines.

I can control my simple non-smart heating solution by manipulating the outdoor temperature data. There a few values that are interesting for me:

* A temperature of **18 degrees or more** will activate "summer mode" that basically will stop heating the radiators.
* With **less than 6 degrees** the system will use an electrical cartridge to boost the system. The heat pump will be exquisitely be used **above** this value.
* If there is **minus 20 or less** outside the electrical cartridge will be exquisitely used.

At midnight I will do a few simulations with different heating profiles over the next 24 hours. Manual and automatic adjustment can be made over the day if the need arises.

This is still really experimental software, I expect this code base to evolve over the winter while I use it. This project is quite specific for my needs, but it may help you get doing with a similar solution of your own.
