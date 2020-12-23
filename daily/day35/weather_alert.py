import datetime as dt
import json
import logging
import os
from typing import List, NamedTuple

import requests
from twilio.rest import Client

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class TwilioCreds(NamedTuple):
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str


class WeatherData(NamedTuple):
    time: dt.datetime
    id: int
    main: str
    temperature: float
    description: str


# Wh = namedtuple("weather_data", ["time", "id", "main", "temperature", "description"])


class WeatherAlerter:
    """ Simple framework for responding to weathers
        Currently just send alert if target weather is detected in the next 24 hours
    """

    OPENWEATHER_CRED = "./secret/openweather_creds.json"
    TWILIO_CRED = "./secret/twilio_creds.json"
    SNOW = 600
    THUNDERSTORM = 200
    CLOUDY = 800

    def __init__(self, _lat: float, _lon: float, hour: int = 24):
        self._lat: float = _lat
        self._lon: float = _lon
        self._hour: int = hour
        self._weather_api_key: str = self._load_weather_creds(self.OPENWEATHER_CRED)
        self._twilio_creds: TwilioCreds = self._load_twilio_creds(self.TWILIO_CRED)

        self.twilio_client: Client = self._make_twilio_client(self._twilio_creds)

    @staticmethod
    def _make_twilio_client(twilio_creds: TwilioCreds):
        return Client(twilio_creds.account_sid, twilio_creds.auth_token)

    @staticmethod
    def _load_weather_creds(cred_loc: str):
        with open(cred_loc, "r") as fp:
            return json.load(fp)["key"]

    @staticmethod
    def _load_twilio_creds(cred_loc: str) -> TwilioCreds:
        with open(cred_loc, "r") as fp:
            creds = json.load(fp)
            return TwilioCreds(**creds)

    def query_hourly_weather(self):
        skip_part = ",".join(["current", "minutely", "daily"])
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/onecall?lat={self._lat}&lon={self._lon}&exclude={skip_part}&appid={self._weather_api_key}&units=metric"
        )
        response.raise_for_status()
        hourly_data = response.json()["hourly"]
        return hourly_data[: self._hour]

    @staticmethod
    def _is_within_range(target_id: int, check_id: int) -> bool:
        """ check weather condition id, e.g. 6xx refers to snow
            See https://openweathermap.org/weather-conditions
        """
        return check_id > target_id and check_id < target_id + 100

    @staticmethod
    def _make_message(hourly_matches: List):
        times = [h.time for h in hourly_matches]
        min_time, max_time = min(times), max(times)
        worst = sorted(hourly_matches, key=lambda x: x.id)[-1]
        condition = hourly_matches[0].main
        message = f"Expect {condition.lower()} from {min_time:%I:%m%p} to {max_time:%I:%m%p}\n"
        message += f"Worst at {worst.time:%I:%m%p} with {worst.description} at {worst.temperature}C"
        return message

    def check_target_condition(self, target: int):
        hourly_data = self.query_hourly_weather()
        hourly_matches = []

        for hour_item in hourly_data:
            time = dt.datetime.fromtimestamp(hour_item["dt"])
            temp = hour_item["temp"]
            for weather in hour_item["weather"]:
                wid = weather["id"]
                if self._is_within_range(target, wid):
                    hourly_matches.append(
                        WeatherData(
                            time, wid, weather["main"], temp, weather["description"]
                        )
                    )
        if hourly_matches:
            self.send_message(self._make_message(hourly_matches))
        else:
            logger.info("no targeted weather found, no message sent")

    def send_message(self, message_body: str):
        logger.info("sending message")
        message = self.twilio_client.messages.create(
            from_=self._twilio_creds.from_number,
            to=self._twilio_creds.to_number,
            body=message_body,
        )
        logger.info(f"message sent with {message.sid} with status {message.status}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{__name__}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    wa = WeatherAlerter(41.881832, -87.623177)
    wa.check_target_condition(WeatherAlerter.SNOW)
