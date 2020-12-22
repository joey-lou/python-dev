import base64
import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


class Oauth2Runner:
    """ Authenticator for google API
    """

    GOOGLE_ACCOUNTS_BASE_URL = "https://accounts.google.com"
    REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
    DEFAULT_SCOPE = "https://mail.google.com/"
    DEFAULT_CRED_PATH = "./secret/creds.json"  # user specific path

    def __init__(
        self,
        client_id,
        client_secret,
        username,
        refresh_token=None,
        access_token=None,
        scope=None,
        cred_file_loc=None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.scope = scope or self.DEFAULT_SCOPE
        self.cred_file_loc = cred_file_loc or self.DEFAULT_CRED_PATH

    @classmethod
    def from_serializable(cls, json_dict):
        return Oauth2Runner(
            json_dict.get("client_id"),
            json_dict.get("client_secret"),
            json_dict.get("username"),
            json_dict.get("refresh_token"),
            json_dict.get("access_token"),
        )

    @classmethod
    def from_json_file(cls, json_file_loc=None):
        try:
            file_loc = json_file_loc or cls.DEFAULT_CRED_PATH
            with open(file_loc, "r") as json_file:
                json_dict = json.load(json_file)
            logger.info(f"read creds from {file_loc}")
        except FileNotFoundError as e:
            logger.error(e)
            json_dict = {}
        return cls.from_serializable(json_dict)

    def to_serializable(self,):
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "refresh_token": self.refresh_token,
            "access_token": self.access_token,
        }

    def save_cred_to_file(self):
        serialized = self.to_serializable()
        with open(self.cred_file_loc, "w") as json_file:
            json.dump(serialized, json_file, indent=4)
        logger.info(f"saved creds to {self.cred_file_loc}")

    @staticmethod
    def _command_to_url(command):
        return "%s/%s" % (Oauth2Runner.GOOGLE_ACCOUNTS_BASE_URL, command)

    @staticmethod
    def _url_escape(text):
        return urllib.parse.quote(text, safe="~-._")

    @staticmethod
    def url_unescape(text):
        return urllib.parse.unquote(text)

    @staticmethod
    def _url_format_params(params):
        param_fragments = []
        for param in sorted(params.items(), key=lambda x: x[0]):
            param_fragments.append(
                "%s=%s" % (param[0], Oauth2Runner._url_escape(param[1]))
            )
        return "&".join(param_fragments)

    def _permission_url(self):
        params = {}
        params["client_id"] = self.client_id
        params["redirect_uri"] = self.REDIRECT_URI
        params["scope"] = self.scope
        params["response_type"] = "code"
        return "%s?%s" % (
            self._command_to_url("o/oauth2/auth"),
            self._url_format_params(params),
        )

    def _verify_tokens(self, verification_code):
        assert (
            verification_code
        ), "must have verification code input to obtain autorization tokens"
        params = {}
        params["client_id"] = self.client_id
        params["client_secret"] = self.client_secret
        params["code"] = verification_code
        params["redirect_uri"] = self.REDIRECT_URI
        params["grant_type"] = "authorization_code"
        request_url = self._command_to_url("o/oauth2/token")
        response = (
            urllib.request.urlopen(
                request_url, urllib.parse.urlencode(params).encode("UTF-8")
            )
            .read()
            .decode("UTF-8")
        )
        return json.loads(response)

    def refresh_authorization(self,):
        logger.info("trying to refresh authorization..")
        assert self.refresh_token, "refresh token not set"
        params = {}
        params["client_id"] = self.client_id
        params["client_secret"] = self.client_secret
        params["refresh_token"] = self.refresh_token
        params["grant_type"] = "refresh_token"
        request_url = self._command_to_url("o/oauth2/token")
        response = (
            urllib.request.urlopen(
                request_url, urllib.parse.urlencode(params).encode("UTF-8")
            )
            .read()
            .decode("UTF-8")
        )
        response = json.loads(response)
        logger.info(f"obtained access token, which expires in {response['expires_in']}")
        return response["access_token"]

    def generate_oauth2_string(self, as_base64=True):
        auth_string = "user=%s\1auth=Bearer %s\1\1" % (self.username, self.access_token)
        if as_base64:
            auth_string = base64.b64encode(auth_string.encode("ascii")).decode("ascii")
        return auth_string

    def generate_new_oauth2_string(self, as_base64=True):
        try:
            self.access_token = self.refresh_authorization()
        except Exception as e:
            logger.error(
                f"received following error while refreshing authorization:\n{e}"
            )
            self.refresh_token, self.access_token = self.get_authorization()
        return self.generate_oauth2_string(as_base64)

    def get_authorization(self):
        logger.info("Obtaining new authorization")
        logger.info(
            "Navigate to the following URL to auth:", self._permission_url(),
        )
        verification_code = input("Enter verification code: ")
        logger.info(f"verification token input: {verification_code}")
        response = self._verify_tokens(verification_code)
        logger.info(f"responded with access token {response['access_token']}")
        return response["refresh_token"], response["access_token"]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{__name__}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    oauth2_runner = Oauth2Runner.from_json_file()
    oauth2_str = oauth2_runner.generate_oauth2_string()
    logger.info(f"got oauth2: {oauth2_str}")
    oauth2_runner.save_cred_to_file()
