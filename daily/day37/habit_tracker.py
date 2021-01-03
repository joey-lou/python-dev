import datetime as dt
import json
import logging
import os
import random
import uuid
import webbrowser
from dataclasses import dataclass
from functools import wraps
from itertools import chain
from typing import Dict, Optional

import requests
from typing_extensions import Literal

from tools.consts import PIXELA_CREDS
from tools.utils import read_json_file, write_json_file

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


@dataclass
class PixelaCreds:
    """ manages the credentials state in a dumm way:
        no checkings will be done, we assume the states are tracked properly
        by the user
    """

    token: str
    username: str
    activated: bool
    graphs: Dict[str, str]

    def deactivate(self):
        # clear all info
        self.activated = False
        self.graphs = {}
        self.username = ""
        self.token = ""

    def activate(self, username: str, token: str):
        self.username = username
        self.token = token
        self.activated = True

    def add_graph(self, graph_id: str, graph_name: str):
        self.graphs[graph_name] = graph_id

    def remove_graph(self, graph_name: str):
        del self.graphs[graph_name]

    def has_graph(self, graph_name: str):
        return graph_name in self.graphs

    @property
    def active(self):
        return self.activated

    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_null(cls):
        return cls("", "", False, {})


@dataclass
class Pixel:
    date: str
    quantity: str

    def as_dict(self):
        return self.__dict__


def assert_active(func):
    # assert instance method is called when user is active
    @wraps(func)
    def check_active(self, *args, **kwargs):
        assert self._creds.active, f"{func.__name__} must be called when user is active"
        return func(self, *args, **kwargs)

    return check_active


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PixelaManager:
    """ As the service relies on a consistent credential history, we will only
        allow initialization from local cred file.
        This allows us to update the credentials on the go and remember the changes.
    """

    def __init__(self, cred_loc: str = PIXELA_CREDS):
        self._cred_loc = cred_loc
        self._creds: PixelaCreds = self._load_json()

    def _load_json(self):
        try:
            return PixelaCreds(**read_json_file(self._cred_loc))
        except FileNotFoundError:
            return PixelaCreds.from_null()

    def _update_creds(self):
        write_json_file(self._cred_loc, self._creds.as_dict())

    @staticmethod
    def random_graph_id():
        """ [a-z][a-z0-9-]{1,16}
        """
        random_length = random.randint(5, 15)  # at least 6 char
        first_char = random.choice([chr(i) for i in range(97, 123)])
        all_chars = [chr(i) for i in chain(range(48, 58), range(97, 123), [45])]
        return "".join([first_char] + random.choices(all_chars, k=random_length))

    @staticmethod
    def activate_pixela(username: str):
        token = str(uuid.uuid4())
        r = requests.post(
            "https://pixe.la/v1/users",
            json={
                "username": username,
                "token": token,
                "agreeTermsOfService": "yes",
                "notMinor": "yes",
            },
        )
        response = json.loads(r.text)
        return response, token

    @staticmethod
    def decativate_pixela(username: str, token: str):
        r = requests.delete(
            f"https://pixe.la/v1/users/{username}", headers={"X-USER-TOKEN": token}
        )
        response = json.loads(r.text)
        return response

    @staticmethod
    def create_graph(
        username: str,
        token: str,
        graph_name: str,
        unit: str,
        qty_type: Literal["int", "float"],
        color: str,
    ):
        """ check https://docs.pixe.la/entry/post-graph
        """
        graph_id = PixelaManager.random_graph_id()
        r = requests.post(
            f"https://pixe.la/v1/users/{username}/graphs",
            headers={"X-USER-TOKEN": token},
            json={
                "id": graph_id,
                "name": graph_name,
                "unit": unit,
                "type": qty_type,
                "color": color,
            },
        )
        response = json.loads(r.text)
        return response, graph_id

    @staticmethod
    def graph_link(username: str, graph_id: str):
        return f"https://pixe.la/v1/users/{username}/graphs/{graph_id}.html"

    @staticmethod
    def delete_graph(username: str, token: str, graph_id: str):
        """ check https://docs.pixe.la/entry/delete-graph
        """
        r = requests.delete(
            f"https://pixe.la/v1/users/{username}/graphs/{graph_id}",
            headers={"X-USER-TOKEN": token},
        )
        response = json.loads(r.text)
        return response

    @staticmethod
    def user_link(username: str):
        return f"https://pixe.la/@{username}"

    @staticmethod
    def add_pixel(username: str, token: str, graph_id: str, pixel: Pixel):
        r = requests.post(
            f"https://pixe.la/v1/users/{username}/graphs/{graph_id}",
            headers={"X-USER-TOKEN": token},
            json=pixel.as_dict(),
        )
        response = json.loads(r.text)
        return response

    def activate(self, username: str):
        if self._creds.active == True:
            logger.info(
                f"account already activated with username: {self._creds.username}"
            )
            return
        response, token = self.activate_pixela(username)
        if response["isSuccess"] == False:
            raise RuntimeError(response["message"])
        else:
            logger.info(f"account created with response: {response['message']}")
            self._creds.activate(username, token)
            self._update_creds()

    @assert_active
    def deactivate(self):
        # does not seem to have access
        response = self.decativate_pixela(self._creds.username, self._creds.token)
        if response["isSuccess"] == False:
            raise RuntimeError(response["message"])
        else:
            logger.info(f"account deleted with response: {response['message']}")
            self._creds.deactivate()
            self._update_creds()

    @assert_active
    def open_user_page(self):
        link = self.user_link(self._creds.username)
        logger.info(f"user page found at link: {link}")
        webbrowser.open(link)
        return link

    @assert_active
    def new_graph(
        self,
        graph_name: str,
        unit: str = "unit",
        qty_type: Literal["int", "float"] = "int",
        color: str = "shibafu",
    ):
        if self._creds.has_graph(graph_name):
            logger.error(f"{graph_name} already exist for user {self._creds.username}")
            return
        response, graph_id = self.create_graph(
            self._creds.username, self._creds.token, graph_name, unit, qty_type, color
        )
        if response["isSuccess"] == False:
            raise RuntimeError(response["message"])
        else:
            logger.info(f"graph created with response: {response['message']}")
            self._creds.add_graph(graph_id, graph_name)
            self._update_creds()

    @assert_active
    def open_graph_by_name(self, graph_name: Optional[str] = None) -> str:
        """ Obtain current user's graph associated with instance
            If no graph_name is provided, try choosing random id from existing graphs
            Link to graph will be printed
        """
        if graph_name and not self._creds.has_graph(graph_name):
            logger.error(
                f"no graph found with name '{graph_name}' for user '{self._creds.username}'"
            )
            return
        graph_name = graph_name or next(iter(self._creds.graphs), None)
        if not graph_name:
            logger.error(f"no graph associated with user '{self._creds.username} yet")
            return
        link = self.graph_link(self._creds.username, self._creds.graphs[graph_name])
        logger.info(f"graph found at link: {link}")
        webbrowser.open(link)
        return link

    @assert_active
    def delete_graph_by_name(self, graph_name: str):
        if self._creds.has_graph(graph_name):
            response = self.delete_graph(
                self._creds.username, self._creds.token, self._creds.graphs[graph_name]
            )
            if response["isSuccess"] == False:
                raise RuntimeError(response["message"])
            else:
                logger.info(f"graph deleted with response: {response['message']}")
                self._creds.remove_graph(graph_name)
                self._update_creds()
        else:
            logger.error(
                f"graph {graph_name} not found for user {self._creds.username}"
            )

    @assert_active
    def delete_all_graphs(self):
        for graph_name in list(self._creds.graphs):
            self.delete_graph_by_name(graph_name)
        logger.info("successfully deleted all graphs!")

    @assert_active
    def add_pixel_for_graph(
        self, graph_name: str, qty: float, date: Optional[dt.date] = None
    ):
        date = date or dt.date.today()
        date_str = date.strftime("%Y%m%d")
        if self._creds.has_graph(graph_name):
            pixel = Pixel(date_str, str(qty))
            response = self.add_pixel(
                self._creds.username,
                self._creds.token,
                self._creds.graphs[graph_name],
                pixel,
            )
            if response["isSuccess"] == False:
                raise RuntimeError(response["message"])
            else:
                logger.info(
                    f"graph {graph_name} added pixel with response: {response['message']}"
                )
        else:
            logger.error(
                f"cannot insert pixel, graph {graph_name} not found for user {self._creds.username}"
            )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    pm = PixelaManager()
    pm.activate("joey")
    pm.open_user_page()
    pm.new_graph("test")
    pm.open_graph_by_name()
    pm.add_pixel_for_graph("test", 100)
    pm.add_pixel_for_graph("test", 10, dt.date(2021, 1, 1))
    pm.open_graph_by_name()
    pm.delete_all_graphs()
    pm.deactivate()
