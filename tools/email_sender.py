import logging
import smtplib
import traceback
from abc import ABC, abstractmethod
from typing import List, Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .oauth2 import Oauth2Runner
from .utils import SendGridCreds

logger = logging.getLogger(__name__)


class EmailSender(ABC):
    """ Generic parent email sender class
    """

    def __init__(self,):
        pass

    @abstractmethod
    def connect(self):
        return NotImplementedError

    @abstractmethod
    def disconnect(self):
        return NotImplementedError

    @abstractmethod
    def send(self, *args, **kwargs):
        return NotImplementedError

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            return False
        self.disconnect()
        return True


class GmailSender(EmailSender):
    """ Gmail sender, authentication will be automatically invoked upon
        token refresh error, the updated credentials will be saved to json file
        for later use.
        TODO: forming MIME email inside sender
    """

    GMAIL_SMTP = "smtp.gmail.com:587"

    def __init__(self, oauth2: Optional[Oauth2Runner] = None):
        self.server = smtplib.SMTP(self.GMAIL_SMTP)
        # default to initialize from default path
        self.oauth2 = oauth2 or Oauth2Runner.from_json_file()

    def connect(self):
        logger.info("connecting gmail sender")
        self.authenticate()
        self.server.ehlo(self.oauth2.client_id)
        self.server.starttls()
        response = self.server.docmd("AUTH", "XOAUTH2 " + self.oauth2_str)
        logger.info(response)

    def authenticate(self):
        logger.info("authenticating gmail sender")
        self.oauth2_str = self.oauth2.generate_new_oauth2_string()

    def send(self, to_addrs: List[str], msg):
        self.server.sendmail(self.oauth2.username, to_addrs, msg)

    def disconnect(self):
        logger.info("disconnecting gmail sender")
        self.oauth2.save_cred_to_file()  # auto-update cred file
        self.server.quit()


class GridSender(EmailSender):
    def __init__(self, send_grid_creds: SendGridCreds):
        self._creds = send_grid_creds
        self._client = SendGridAPIClient(self._creds.api_key)

    @classmethod
    def from_creds_file(cls, file_loc: str):
        return cls(SendGridCreds.from_json_file(file_loc))

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send(self, to_emails: Optional[List[str]], subject: str, html_content: str):
        from_email = self._creds.from_email
        to_emails = to_emails or [from_email]
        message = Mail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
        )
        response = self._client.send(message)
        logger.info(f"Response returned status code: {response.status_code}")
