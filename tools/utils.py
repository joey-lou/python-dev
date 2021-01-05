import datetime as dt
import json
import logging
from typing import Dict, List, Optional

import requests
from pydantic import BaseModel
from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioCreds(BaseModel):
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str


class Sheet(BaseModel):
    url: str
    sub_sheets: List[str]


class SheetyCreds(BaseModel):
    token: str
    sheets: Dict[str, Sheet]


class KiwiCreds(BaseModel):
    api_key: str


# utility functions
def read_json_file(file_loc: str):
    logger.info(f"reading json from {file_loc}")
    with open(file_loc, "r") as f:
        return json.load(f)


def write_json_file(file_loc: str, json_obj: Dict):
    logger.info(f"writing to {file_loc}")
    with open(file_loc, "w") as f:
        f.write(json.dumps(json_obj, indent=4))


class TwilioTextSender:
    """ uses Twilio API to send simple text messages to oneself
    """

    def __init__(self, creds: Dict):
        self._creds: TwilioCreds = TwilioCreds(**creds)
        self.client = Client(self._creds.account_sid, self._creds.auth_token)

    @classmethod
    def from_json(cls, file_loc: str):
        return cls(read_json_file(file_loc))

    def send_message(self, message_body: str):
        message = self.client.messages.create(
            from_=self._creds.from_number, to=self._creds.to_number, body=message_body,
        )
        logger.info(f"message sent with {message.sid} with status {message.status}")


class SheetyHandler:
    """ uses sheety API to manage linked google sheets
    """

    def __init__(self, creds: Dict):
        self._creds: SheetyCreds = SheetyCreds(**creds)

    @classmethod
    def from_json(cls, file_loc: str):
        return cls(read_json_file(file_loc))

    def _get_all_subsheets(self, sheet: str):
        """ assume sheet exist, KeyError will be raised if main sheet is not found
        """
        return self._creds.sheets[sheet].sub_sheets

    @staticmethod
    def get_sheet_data(sheet: str, sub_sheet: str, url: str, token: str):
        get_url = f"https://api.sheety.co/{url}/{sheet}/{sub_sheet}"
        r = requests.get(url=get_url, headers={"Authorization": token})
        r.raise_for_status()
        return json.loads(r.text)

    @staticmethod
    def add_row(sheet: str, sub_sheet: str, url: str, token: str, row: Dict):
        post_url = f"https://api.sheety.co/{url}/{sheet}/{sub_sheet}"
        r = requests.post(
            url=post_url, headers={"Authorization": token}, json={"destination": row}
        )
        r.raise_for_status()
        return json.loads(r.text)

    def get_sheet(self, sheet: str, sub_sheet: Optional[str] = None):
        sub_sheet = sub_sheet or next(iter(self._get_all_subsheets(sheet)))
        data = self.get_sheet_data(
            sheet, sub_sheet, self._creds.sheets[sheet].url, self._creds.token
        )
        logger.info(f"found sheet data for {sheet}/{sub_sheet}")
        return data[sub_sheet]

    def add_row_to_sheet(self, sheet: str, sub_sheet: str, row: Dict):
        response = self.add_row(
            sheet, sub_sheet, self._creds.sheets[sheet].url, self._creds.token, row
        )
        logger.info(f"row {row} added to {sheet}/{sub_sheet} with response {response}")


class KiwiHandler:
    """ uses KIWI API to query for flights
        https://tequila.kiwi.com/portal/docs/tequila_api/search_api
    """

    def __init__(self, creds: Dict):
        self._creds: KiwiCreds = KiwiCreds(**creds)

    @classmethod
    def from_json(cls, file_loc: str):
        return cls(read_json_file(file_loc))

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
