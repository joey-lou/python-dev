import datetime as dt
import json
import logging
import os
from typing import List, NamedTuple

import requests
from twilio.rest import Client

from tools.consts import OPENWEATHER_CREDS, TWILIO_CREDS
from tools.utils import TwilioCreds, TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


class WeatherData(NamedTuple):
    time: dt.datetime
    id: int
    main: str
    temperature: float
    description: str


class WeatherAlerter:
    """ Simple framework for responding to weathers
        Currently just send alert if target weather is detected in the next 24 hours
    """

    SNOW = 600
    THUNDERSTORM = 200
    CLOUDY = 800

    def __init__(
        self,
        _lat: float,
        _lon: float,
        open_weather_creds_loc: str,
        twilio_creds_loc: str,
        hour: int = 24,
    ):
        self._lat: float = _lat
        self._lon: float = _lon
        self._hour: int = hour
        self._weather_api_key: str = self._load_weather_creds(open_weather_creds_loc)

        self.text_sender = TwilioTextSender.from_json(twilio_creds_loc)

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
        def day_time(datetime: dt.datetime):
            diff = datetime.day - dt.datetime.now().day
            if diff == 1:
                return f"tomorrow {datetime:%I:%M%p}"
            elif diff == 0:
                return f"today {datetime:%I:%M%p}"
            else:
                raise RuntimeError("only future dates are expected in forecast")

        times = [h.time for h in hourly_matches]
        min_time, max_time = min(times), max(times)
        worst = sorted(hourly_matches, key=lambda x: x.id)[-1]
        condition = hourly_matches[0].main
        message = f"Expect {condition.lower()} from {day_time(min_time)} to {day_time(max_time)}\n"
        message += f"Worst at {day_time(worst.time)} with {worst.description} at {worst.temperature}C"
        return message

    def check_target_condition(self, target: int):
        hourly_data = self.query_hourly_weather()
        hourly_matches = []

        for hour_item in hourly_data:
            time = dt.datetime.fromtimestamp(hour_item["dt"])
            temp = hour_item["temp"]
            for weather in hour_item["weather"]:
                wid = weather["id"]
                logger.debug(f"{temp} celsius at {time}, with wid {wid}")
                if self._is_within_range(target, wid):
                    hourly_matches.append(
                        WeatherData(
                            time, wid, weather["main"], temp, weather["description"]
                        )
                    )
        if hourly_matches:
            self.text_sender.send_message(self._make_message(hourly_matches))
        else:
            logger.info("no targeted weather found, no message sent")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    wa = WeatherAlerter(
        41.881832,
        -87.623177,
        open_weather_creds_loc=OPENWEATHER_CREDS,
        twilio_creds_loc=TWILIO_CREDS,
    )
    wa.check_target_condition(WeatherAlerter.CLOUDY)
