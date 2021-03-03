import abc
import datetime as dt
import logging
import sqlite3
from dataclasses import dataclass
from functools import wraps
from numbers import Number
from typing import Union

logger = logging.getLogger(__name__)


class DbInfo:
    @property
    def url(self):
        raise NotImplementedError


@dataclass
class SqliteInfo(DbInfo):
    db_file: str

    @property
    def url(self):
        return self.db_file


def assert_connected(fn):
    @wraps(fn)
    def is_connected(self, *args, **kwargs):
        assert self.connected, f"{self.__class__.__name__} is not connected"
        return fn(self, *args, **kwargs)

    return is_connected


class DBConnection(abc.ABC):
    def __init__(self, db_info: DbInfo):
        self.db_info = db_info
        self.conn = None
        self.connected = False

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def execute(self, sql: str):
        pass

    @abc.abstractmethod
    def fetch(self, sql: str):
        pass

    def __enter__(self):
        self.connect()
        logger.info(f"{self.__class__.__name__} connected")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        logger.info(f"{self.__class__.__name__} disconnected")


class SqliteConnection(DBConnection):
    def connect(self):
        if not self.connected:
            self.conn = sqlite3.connect(self.db_info.url)
            self.connected = True

    def disconnect(self):
        if self.connected:
            self.conn.close()
            self.connected = False

    @assert_connected
    def execute(self, sql: str) -> int:
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()
        return cur.lastrowid

    @assert_connected
    def fetch(self, sql: str) -> list:
        cur = self.conn.cursor()
        cur.execute(sql)
        return cur.fetchall()


class DBClient(abc.ABC):
    def __init__(self, db_conn: DBConnection):
        self.db_conn = db_conn

    def __enter__(self):
        self.db_conn.connect()
        logger.info(f"{self.__class__.__name__} connected")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_conn.disconnect()
        logger.info(f"{self.__class__.__name__} disconnected")

    @abc.abstractmethod
    def insert(self, table: str, rows: list):
        pass


class SqliteClient(DBClient):
    @classmethod
    def from_db_info(cls, db_info: SqliteInfo):
        return cls(SqliteConnection(db_info))

    @staticmethod
    def _make_row(row: list):
        items = []
        for val in row:
            if isinstance(val, Number):
                items.append(f"{val}")
            elif isinstance(val, str):
                items.append(f"'{val}'")
            elif isinstance(val, Union(dt.datetime, dt.date)):
                items.append(f"'{val}'")
            else:
                raise ValueError(
                    f"Value {val} of type {type(val)} is yet to be handled"
                )
        return "(" + ", ".join(items) + ")"

    def insert(self, table: str, rows: list):
        sql = f""" INSERT INTO '{table}'
                   VALUES {' '.join((self._make_row(r) for r in rows))} """
        rid = self.db_conn.execute(sql)
        logger.info(f"{len(rows)} records added to table {table}, now at row {rid}")

    def get(self, table: str):
        sql = f""" SELECT *
                   FROM {table} """
        return self.db_conn.fetch(sql)
