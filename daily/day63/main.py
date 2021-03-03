import logging
import os
from dataclasses import dataclass

from flask import Flask, render_template, request

from tools.db_utils import SqliteClient, SqliteInfo

ROOT_PATH = os.path.dirname(__file__)
STATIC_PATH = os.path.join(ROOT_PATH, "static")
TEMPLATE_PATH = os.path.join(ROOT_PATH, "templates")
DB_LOC = os.path.join(ROOT_PATH, "library_demo.db")

APP_NAME = "book_shelf"
logger = logging.getLogger(APP_NAME)


@dataclass
class Book:
    name: str
    author: str
    rating: float


app = Flask(APP_NAME, static_folder=STATIC_PATH, template_folder=TEMPLATE_PATH)
app.secret_key = "ABC"


def get_books_from_db(sqlite_client: SqliteClient):
    rows = sqlite_client.get("library")
    all_books = []
    for row in rows:
        all_books.append(Book(*row))
    return all_books


@app.route("/")
def home():
    with SqliteClient.from_db_info(SqliteInfo(DB_LOC)) as sqlite_client:
        return render_template("index.html", books=get_books_from_db(sqlite_client))


@app.route("/add", methods=["POST", "GET"])
def add():
    if request.method == "POST":
        rform = request.form
        with SqliteClient.from_db_info(SqliteInfo(DB_LOC)) as sqlite_client:
            sqlite_client.insert(
                "library", [[rform["name"], rform["author"], rform["rating"]]]
            )
        return render_template("add.html", success=True)
    return render_template("add.html", success=False)


if __name__ == "__main__":
    app.run(debug=True)
