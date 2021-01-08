import datetime as dt
import logging
import os
from dataclasses import dataclass
from typing import Dict, List

from tools.consts import KIWI_CREDS, SHEETY_CREDS, TWILIO_CREDS
from tools.utils import KiwiHandler, SheetyHandler, TwilioTextSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


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
        SheetyHandler.from_json(SHEETY_CREDS),
        TwilioTextSender.from_json(TWILIO_CREDS),
        KiwiHandler.from_json(KIWI_CREDS),
    )
    cff.run()
