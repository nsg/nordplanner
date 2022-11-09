import pytest
import utils


def test_get_temp_decrease_value():
    assert utils.get_temp_decrease_value(10, 20, 30) == 19.67
    assert utils.get_temp_decrease_value(5, 20, 30) == 19.5
    assert utils.get_temp_decrease_value(-8, 20, 30) == 19.07
    assert utils.get_temp_decrease_value(-15, 20, 30) == 18.83


def test_get_temp_increase_value():
    assert utils.get_temp_increase_value(10, 20, 14, 1, 30) == 21.07
    assert utils.get_temp_increase_value(5, 20, 14, 1, 30) == 20.43
    assert utils.get_temp_increase_value(-8, 20, 14, 1, 30) == 20.57
    assert utils.get_temp_increase_value(-15, 20, 14, 1, 30) == 20.23


def test_plan_day():
    yr = [9] * 6 + [4] * 8 + [-2] * 5 + [0] + [2] * 4
    nordpool = [
        10,
        10,
        12,
        12,
        10,
        10,
        15,
        25,
        40,
        50,
        60,
        60,
        50,
        40,
        50,
        60,
        30,
        30,
        20,
        20,
        18,
        15,
        10,
        10,
    ]
    config = {
        "temp_increase_constant": 14,
        "temp_increase_constant_boost": 1,
        "temp_decrease_constant": 40,
    }
    plan = {
        "max_price": 35,
        "hours": [
            {
                "target": 9,
                "price": 10,
                "active": True,
                "indoor_forecast": "19.0",
                "outdoor_forecast": 9,
            },
            {
                "target": 9,
                "price": 10,
                "active": True,
                "indoor_forecast": "20.1",
                "outdoor_forecast": 9,
            },
            {
                "target": 9,
                "price": 12,
                "active": True,
                "indoor_forecast": "21.1",
                "outdoor_forecast": 9,
            },
            {
                "target": 9,
                "price": 12,
                "active": True,
                "indoor_forecast": "22.0",
                "outdoor_forecast": 9,
            },
            {
                "target": 20,
                "price": 10,
                "active": False,
                "indoor_forecast": "22.7",
                "outdoor_forecast": 9,
            },
            {
                "target": 20,
                "price": 10,
                "active": False,
                "indoor_forecast": "22.4",
                "outdoor_forecast": 9,
            },
            {
                "target": 20,
                "price": 15,
                "active": False,
                "indoor_forecast": "22.1",
                "outdoor_forecast": 4,
            },
            {
                "target": 4,
                "price": 25,
                "active": True,
                "indoor_forecast": "21.6",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 40,
                "active": False,
                "indoor_forecast": "23.0",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 50,
                "active": False,
                "indoor_forecast": "22.5",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 60,
                "active": False,
                "indoor_forecast": "22.0",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 60,
                "active": False,
                "indoor_forecast": "21.6",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 50,
                "active": False,
                "indoor_forecast": "21.1",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 40,
                "active": False,
                "indoor_forecast": "20.7",
                "outdoor_forecast": 4,
            },
            {
                "target": 20,
                "price": 50,
                "active": False,
                "indoor_forecast": "20.3",
                "outdoor_forecast": -2,
            },
            {
                "target": 20,
                "price": 60,
                "active": False,
                "indoor_forecast": "19.7",
                "outdoor_forecast": -2,
            },
            {
                "target": -2,
                "price": 30,
                "active": True,
                "indoor_forecast": "19.2",
                "outdoor_forecast": -2,
            },
            {
                "target": -2,
                "price": 30,
                "active": True,
                "indoor_forecast": "20.3",
                "outdoor_forecast": -2,
            },
            {
                "target": -2,
                "price": 20,
                "active": True,
                "indoor_forecast": "21.4",
                "outdoor_forecast": -2,
            },
            {
                "target": 20,
                "price": 20,
                "active": False,
                "indoor_forecast": "22.4",
                "outdoor_forecast": 0,
            },
            {
                "target": 2,
                "price": 18,
                "active": True,
                "indoor_forecast": "21.9",
                "outdoor_forecast": 2,
            },
            {
                "target": 20,
                "price": 15,
                "active": False,
                "indoor_forecast": "23.1",
                "outdoor_forecast": 2,
            },
            {
                "target": 20,
                "price": 10,
                "active": False,
                "indoor_forecast": "22.5",
                "outdoor_forecast": 2,
            },
            {
                "target": 20,
                "price": 10,
                "active": False,
                "indoor_forecast": "22.0",
                "outdoor_forecast": 2,
            },
        ],
    }
    assert utils.plan_day(yr, nordpool, 20, 20, 22, 19, config) == plan
