import random

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "This is the worst page ever!"


@app.route("/menu/<dish>")
def menu(dish):
    return f"{dish} is ${random.randint(5, 40)}!"


@app.route("/projects/")
def project():
    return "projects path will default with end slash"


# quickstart: https://flask.palletsprojects.com/en/1.1.x/quickstart/#quickstart
# run following command for demo
# 1. export FLASK_APP=hello.py (relative path from terminal pwd)
# 2. flask run
# alternatively, run hello.py as main

if __name__ == "__main__":
    app.run(debug=True)
