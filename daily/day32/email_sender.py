import base64
import imaplib
import json
import logging
import os
import smtplib
import urllib.parse
import urllib.request
from abc import ABC, abstractclassmethod, abstractmethod, abstractstaticmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import lxml.html

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)
logging.basicConfig(
    level=logging.DEBUG, format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s"
)


GOOGLE_CLIENT_ID = (
    "308064597116-1ct1khr676pm7toaja3huf6he9o16jcf.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = "6-60tFkI80gSoDE5Fx3knJDS"
GOOGLE_REFRESH_TOKEN = "1//0f8uzKC4b6tPFCgYIARAAGA8SNwF-L9IrZuRyIiTddssChoiX_FrfmYusBBjOBfXgwlSXasZBQ1pJRkAHMtUhigxtvWIslgoaYEI"


class EmailSender(ABC):
    """ Generic parent email sender class
    """

    def __init__(self,):
        pass

    @abstractmethod
    def connect(self):
        return NotImplementedError

    @abstractmethod
    def authenticate(self):
        return NotImplementedError

    @abstractmethod
    def disconnect(self):
        return NotImplementedError

    def __enter__(self):
        self.connect()

    @abstractmethod
    def __exit__(self):
        self.disconnect()


class Oauth2Runner:
    """ Authenticator for google API
    """

    GOOGLE_ACCOUNTS_BASE_URL = "https://accounts.google.com"
    REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
    DEFAULT_SCOPE = "https://mail.google.com/"

    def __init__(self, client_id, client_secret, authorization_code, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_code = authorization_code
        self.scope = scope or self.DEFAULT_SCOPE

    @classmethod
    def from_serializable(cls, json_str):
        return cls.__init__(
            json_str.get("client_id"),
            json_str.get("client_secret"),
            json_str.get("authorization_code"),
        )

    @staticmethod
    def command_to_url(command):
        return "%s/%s" % (Oauth2Runner.GOOGLE_ACCOUNTS_BASE_URL, command)

    @staticmethod
    def url_escape(text):
        return urllib.parse.quote(text, safe="~-._")

    @staticmethod
    def url_unescape(text):
        return urllib.parse.unquote(text)

    @staticmethod
    def url_format_params(params):
        param_fragments = []
        for param in sorted(params.items(), key=lambda x: x[0]):
            param_fragments.append("%s=%s" % (param[0], url_escape(param[1])))
        return "&".join(param_fragments)

    def generate_permission_url(self):
        params = {}
        params["client_id"] = self.client_id
        params["redirect_uri"] = self.REDIRECT_URI
        params["scope"] = self.scope
        params["response_type"] = "code"
        return "%s?%s" % (
            self.command_to_url("o/oauth2/auth"),
            self.url_format_params(params),
        )

    def maunal_verify_tokens(self, verification_code):
        assert (
            verification_code
        ), "must have verification code input to obtain autorization tokens"
        params = {}
        params["client_id"] = self.client_id
        params["client_secret"] = self.client_secret
        params["code"] = verification_code
        params["redirect_uri"] = self.REDIRECT_URI
        params["grant_type"] = "authorization_code"
        request_url = self.command_to_url("o/oauth2/token")
        response = (
            urllib.request.urlopen(
                request_url, urllib.parse.urlencode(params).encode("UTF-8")
            )
            .read()
            .decode("UTF-8")
        )
        return json.loads(response)

    def call_refresh_token(client_id, client_secret, refresh_token):
        params = {}
        params["client_id"] = client_id
        params["client_secret"] = client_secret
        params["refresh_token"] = refresh_token
        params["grant_type"] = "refresh_token"
        request_url = command_to_url("o/oauth2/token")
        response = (
            urllib.request.urlopen(
                request_url, urllib.parse.urlencode(params).encode("UTF-8")
            )
            .read()
            .decode("UTF-8")
        )
        return json.loads(response)

    def generate_oauth2_string(username, access_token, as_base64=False):
        auth_string = "user=%s\1auth=Bearer %s\1\1" % (username, access_token)
        if as_base64:
            auth_string = base64.b64encode(auth_string.encode("ascii")).decode("ascii")
        return auth_string

    def get_authorization(self):
        logger.info(
            "Navigate to the following URL to auth:", self.generate_permission_url(),
        )
        verification_code = input("Enter verification code: ")
        logger.info(f"verification token input: {verification_code}")
        response = self.maunal_verify_tokens(verification_code)
        logger.info(f"responded with access token {response['access_token']}")
        return (
            response["refresh_token"],
            response["access_token"],
            response["expires_in"],
        )

    def refresh_authorization(google_client_id, google_client_secret, refresh_token):
        response = call_refresh_token(
            google_client_id, google_client_secret, refresh_token
        )
        return response["access_token"], response["expires_in"]


def send_mail(fromaddr, toaddr, subject, message):
    access_token, expires_in = refresh_authorization(
        GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
    )
    auth_string = generate_oauth2_string(fromaddr, access_token, as_base64=True)

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg.preamble = "This is a multi-part message in MIME format."
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)
    part_text = MIMEText(
        lxml.html.fromstring(message).text_content().encode("utf-8"),
        "plain",
        _charset="utf-8",
    )
    part_html = MIMEText(message.encode("utf-8"), "html", _charset="utf-8")
    msg_alternative.attach(part_text)
    msg_alternative.attach(part_html)
    server = smtplib.SMTP("smtp.gmail.com:587")
    server.ehlo(GOOGLE_CLIENT_ID)
    server.starttls()
    server.docmd("AUTH", "XOAUTH2 " + auth_string)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()


if __name__ == "__main__":
    if GOOGLE_REFRESH_TOKEN is None:
        print("No refresh token found, obtaining one")
        refresh_token, access_token, expires_in = get_authorization(
            GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
        )
        print("Set the following as your GOOGLE_REFRESH_TOKEN:", refresh_token)
        exit()

    send_mail(
        "richardlou99@gmail.com",
        "richardlou99@gmail.com",
        "A mail from you from Python",
        "<b>A mail from you from Python</b><br><br>" + "So happy to hear from you!",
    )
