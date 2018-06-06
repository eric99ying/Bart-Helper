"""Bart Helper lambda function code, which is triggered by HTTPS calls from Api.ai to the Api gateway."""
import json
import requests
import os
import stations
from utils import get_station_name, get_direction


BART_URL = "http://api.bart.gov/api/etd.aspx"

def lambda_handler(event, context):
    """Takes in an event from Api.ai, through Api Gateway.
    Returns a dict with keys "speech", "displayText", and "Source".
    Source is always the "BART API"    """
    station_name = get_station_name(event)
    spoken_station_name = station_info(station_name)["spoken_name"]
    written_station_name = station_info(station_name)["written_name"]
    direction = get_direction(event)[0].lower()

    """Sets the parameters of the request to the bart api."""
    param = {}
    param["cmd"] = "etd"
    param["orig"] = station_info(station_name)["abbr"]
    param["key"] = os.environ["BART_API_KEY"]
    param["dir"] = direction
    param["json"] = "y"

    response = requests.get(BART_URL, params = param)
    response_json = response.json()

    minutes = get_departure_info(response_json)["minutes"]
    minutes_next = get_departure_info(response_json)["minutes next"]
    destination = get_departure_info(response_json)["destination"]
    spoken_text = get_spoken_or_written_string(spoken_station_name, direction, minutes, destination, minutes_next, True)
    written_text = get_spoken_or_written_string(written_station_name, direction, minutes, destination, minutes_next, False)

    return {"speech" : spoken_text, "display API" : written_text, "source" : "BART API"}

def station_info(station_name):
    """Returns the station info given a station name.

    Args:
        station(str) : The station name.
    Returns:
        dict: The station info as a dict. 
    """
    for st in stations.stations:
        if st["api_ai_value"] == station_name:
            return st

    raise ValueError("Invalid station name.")

def get_departure_info(input_json):
    """Returns the number of minutes until the next train arrives.

    Args:
        input_json(json) : The json from the Bart API.
    Returns:
        dict : The departure info.
            "destination" : The destination of the train.
            "minutes" : The number of minutes until the train arrives."""
    departure_info = {}
    departure_info["destination"] = input_json["root"]["station"][0]["etd"][0]["destination"]
    departure_info["minutes"] = input_json["root"]["station"][0]["etd"][0]["estimate"][0]["minutes"]
    departure_info["minutes next"] = input_json["root"]["station"][0]["etd"][0]["estimate"][1]["minutes"]
    return departure_info


def get_spoken_or_written_string(name, direction, minutes, destination, minutes_next, spoken):
    """Returns the spoken string given a station name and direction.

    Args:
        name(str) : The station name.
        direction(str) : The given direction.
        minutes(str) : The minutes until next train.
        destination(str) : The destination of the next train.
        minutes_next(str) : The number of minutes until the second train arrives.
        spoken(bool) : If the user wants spoken string or written string.
    Returns:
        str: The spoken string. 
    """
    dir = ""

    if direction == "n":
        if spoken:
            dir = "north bound"
        else:
            dir = "North-bound"
    else:
        if spoken:
            dir = "south bound"
        else:
            dir = "South-bound"

    second_half_text_first = "leaves " + name + " in " + minutes + " minutes."
    if minutes == "0" or minutes == "Leaving":
        second_half_text_first = "leaving " + name + " is arriving now."

    second_half_text_second = "leaves " + name + " in " + minutes_next + " minutes."
    if minutes_next == "0" or minutes_next == "Leaving":
        second_half_text_second = "leaving " + name + " is arriving now."

    return "The next " + dir + " train " + second_half_text_first \
        + " Then, another " + dir + " train " + second_half_text_second


def test_lambda_handler():
    """This may be helpful when testing your function"""
    with open(file='sample_event.json', mode='r') as f:
        sample_event = json.load(f)

    response = lambda_handler(sample_event, None)
    print(json.dumps(response, indent=4))


if __name__ == '__main__':
    test_lambda_handler()
