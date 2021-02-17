import logging
import os

from flask import Flask, render_template

ROOT_PATH = os.path.dirname(__file__)
APP_NAME = "personal_site"
app = Flask(APP_NAME, root_path=ROOT_PATH)
logger = logging.getLogger(APP_NAME)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    app.run(debug=True)
