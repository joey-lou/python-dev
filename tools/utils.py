import json
import logging
from typing import Dict, NamedTuple

from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioCreds(NamedTuple):
    account_sid: str
    auth_token: str
    from_number: str
    to_number: str


class TwilioTextSender:
    """ uses Twilio API to send simple text messages to oneself
    """

    def __init__(self, creds: Dict):
        self._creds: TwilioCreds = TwilioCreds(**creds)
        self.client = Client(self._creds.account_sid, self._creds.auth_token)

    @classmethod
    def from_json(cls, file_loc: str):
        with open(file_loc, "r") as fp:
            creds = json.load(fp)
            return cls(creds)

    def send_message(self, message_body: str):
        message = self.client.messages.create(
            from_=self._creds.from_number, to=self._creds.to_number, body=message_body,
        )
        logger.info(f"message sent with {message.sid} with status {message.status}")


# utility functions
def read_json_file(file_loc: str):
    logger.info(f"reading json from {file_loc}")
    with open(file_loc, "r") as f:
        return json.load(f)


def write_json_file(file_loc: str, json_obj: Dict):
    logger.info(f"writing to {file_loc}")
    with open(file_loc, "w") as f:
        f.write(json.dumps(json_obj, indent=4))
