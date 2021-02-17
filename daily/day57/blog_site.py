import datetime as dt
import json
import logging
import os

import requests
from flask import Flask, render_template

ROOT_PATH = os.path.dirname(__file__)
APP_NAME = "personal_blog_site"
app = Flask(APP_NAME, root_path=ROOT_PATH)
logger = logging.getLogger(APP_NAME)


@app.route("/")
def home():
    return render_template("index.html", date=dt.date.today())


@app.route("/guess/<name>")
def your_page(name: str):
    res = requests.get(f"https://api.agify.io?name={name}")
    age = json.loads(res.content)["age"]

    res = requests.get(f"https://api.genderize.io?name={name}")
    gender = json.loads(res.content)["gender"]
    return render_template("name.html", name=name, age=age, gender=gender)


@app.route("/blogs/<int:blog_id>")
def blog_post(blog_id):
    return render_template(
        "post.html", blog=fake_blogs[blog_id - 1], date=dt.date.today()
    )


@app.route("/blogs")
def blogs():
    return render_template("blogs.html", blogs=fake_blogs, date=dt.date.today())


fake_blogs = [
    {
        "id": 1,
        "title": "The Life of Cactus",
        "subtitle": "Who knew that cacti lived such interesting lives.",
        "body": "Nori grape silver beet broccoli kombu beet greens fava bean potato quandong celery. Bunya nuts black-eyed pea prairie turnip leek lentil turnip greens parsnip. Sea lettuce lettuce water chestnut eggplant winter purslane fennel azuki bean earthnut pea sierra leone bologi leek soko chicory celtuce parsley jícama salsify.",
    },
    {
        "id": 2,
        "title": "Top 15 Things to do When You are Bored",
        "subtitle": "Are you bored? Don't know what to do? Try these top 15 activities.",
        "body": "Chase ball of string eat plants, meow, and throw up because I ate plants going to catch the red dot today going to catch the red dot today. I could pee on this if I had the energy. Chew iPad power cord steal the warm chair right after you get up for purr for no reason leave hair everywhere, decide to want nothing to do with my owner today.",
    },
    {
        "id": 3,
        "title": "Introduction to Intermittent Fasting",
        "subtitle": "Learn about the newest health craze.",
        "body": "Cupcake ipsum dolor. Sit amet marshmallow topping cheesecake muffin. Halvah croissant candy canes bonbon candy. Apple pie jelly beans topping carrot cake danish tart cake cheesecake. Muffin danish chocolate soufflé pastry icing bonbon oat cake. Powder cake jujubes oat cake. Lemon drops tootsie roll marshmallow halvah carrot cake.",
    },
]
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    app.run(debug=True)
