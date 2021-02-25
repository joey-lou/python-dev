import datetime as dt
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

from tools.consts import KIWI_CREDS, SHEETY_CREDS, TWILIO_CREDS
from tools.utils import BaseCreds, SheetyHandler, TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)

# ~~~~~~~~~~~~~~~~ KIWI handler ~~~~~~~~~~~~~~~~~~
class KiwiCreds(BaseCreds):
    api_key: str


class KiwiHandler:
    """ uses KIWI API to query for flights
        https://tequila.kiwi.com/portal/docs/tequila_api/search_api
    """

    def __init__(self, kiwi_creds: KiwiCreds):
        self._creds: KiwiCreds = kiwi_creds

    @classmethod
    def from_creds_file(cls, file_loc: str):
        return cls(KiwiCreds.from_json_file(file_loc))

    @staticmethod
    def search_flight(
        api_key: str,
        start_date: dt.date,
        end_date: dt.date,
        from_airport: str,
        to_airport: str,
        search_by_city: bool,
        currency: str,
    ):
        from_airport = f"{'city:' if search_by_city else ''}{from_airport}"
        to_airport = f"{'city:' if search_by_city else ''}{to_airport}"
        get_url = f"https://tequila-api.kiwi.com/v2/search?curr={currency}&fly_from={from_airport}&fly_to={to_airport}&dateFrom={start_date:%d/%m/%Y}&dateTo={end_date:%d/%m/%Y}"
        r = requests.get(url=get_url, headers={"apikey": api_key})
        r.raise_for_status()
        response = json.loads(r.text)
        logger.info(f"queried flight with params {response['search_params']}")
        return response["data"]

    def flight_next_n_months(
        self,
        from_airport: str,
        to_airport: str,
        n: int = 3,
        start_date: Optional[dt.date] = None,
        search_by_city: bool = True,
        currency: str = "USD",
    ):
        start_date = start_date or dt.date.today()
        end_date = start_date + dt.timedelta(days=n * 30)
        return self.search_flight(
            self._creds.api_key,
            start_date,
            end_date,
            from_airport,
            to_airport,
            search_by_city,
            currency,
        )


# ~~~~~~~~~~~~~~~~ Flight Finder Application ~~~~~~~~~~~~~~~~~~


@dataclass
class Target:
    airport: str
    price: float


@dataclass
class Flight:
    airlines: List[str]
    city_from: str
    city_to: str
    airport_from: str
    airport_to: str
    price: float
    local_depart: dt.datetime
    local_arrive: dt.datetime
    link: str

    @classmethod
    def from_json(cls, data: Dict):
        return cls(
            airlines=data["airlines"],
            city_from=data["cityFrom"],
            city_to=data["cityTo"],
            airport_from=data["flyFrom"],
            airport_to=data["flyTo"],
            price=data["price"],
            local_depart=dt.datetime.fromisoformat(data["local_departure"].rstrip("Z")),
            local_arrive=dt.datetime.fromisoformat(data["local_arrival"].rstrip("Z")),
            link=data["deep_link"],
        )

    def print_msg(self):
        return (
            f"Flight from {self.city_from} ({self.airport_from}) at {self.local_depart} "
            f"to {self.city_to} ({self.airport_to}) at {self.local_arrive} is only ${self.price:,.1f}!"
        )


class CheapFlightFinder:
    """ finds cheap flight and send alert based on our threshold
        1. service will run and query google sheet for all detinations that it is tracking
        2. check flight prices for next 6 months of the tracked destinations using kiwi
        3. alert user if tickets cheaper than price set in google sheet is found
    """

    SHEET = "pydevD39CheapFlight"
    DESTINATION_SHEET = "destinations"
    BASE_AIRPORT = "ORD"

    def __init__(
        self,
        sheety_handler: SheetyHandler,
        twilio_sender: TwilioTextSender,
        kiwi_handler: KiwiHandler,
    ):
        self.shh: SheetyHandler = sheety_handler
        self.tws: TwilioTextSender = twilio_sender
        self.kwh: KiwiHandler = kiwi_handler

    def _query_destination_airports(self):
        destinations = self.shh.get_sheet(self.SHEET, self.DESTINATION_SHEET)
        targets = []
        for dest_dict in destinations:
            targets.append(
                Target(airport=dest_dict["airport"], price=dest_dict["price"])
            )
        return targets

    def run(self):
        for target in self._query_destination_airports():
            cheapeast_flight = self.kwh.flight_next_n_months(
                from_airport=self.BASE_AIRPORT, to_airport=target.airport, n=3
            )[0]
            flight = Flight.from_json(cheapeast_flight)
            if flight.price <= target.price:
                logger.info(f"found an desired flight {flight}")
                msg = flight.print_msg()
                self.tws.send_message(msg)
                logger.info(f"message sent: {msg}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    cff = CheapFlightFinder(
        SheetyHandler.from_creds_file(SHEETY_CREDS),
        TwilioTextSender.from_creds_file(TWILIO_CREDS),
        KiwiHandler.from_creds_file(KIWI_CREDS),
    )
    cff.run()
