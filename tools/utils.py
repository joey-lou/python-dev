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
