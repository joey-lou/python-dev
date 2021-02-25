import datetime as dt
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict

from flask import Flask, render_template, request

from tools.consts import GRID_CREDS
from tools.email_sender import GmailSender, GridSender

ROOT_PATH = os.path.dirname(__file__)
STATIC_PATH = os.path.join(ROOT_PATH, "../day59/static")  # share same static files
TEMPLATE_PATH = os.path.join(ROOT_PATH, "templates")

APP_NAME = "personal_blog_site"
app = Flask(APP_NAME, static_folder=STATIC_PATH, template_folder=TEMPLATE_PATH)
logger = logging.getLogger(APP_NAME)


@app.route("/")
def home():
    return render_template("index.html", date=dt.date.today(), blogs=fake_blogs)


@app.route("/blogs/<int:blog_id>")
def blog_post(blog_id):
    return render_template(
        "post.html", blog=fake_blogs[blog_id - 1], date=dt.date.today()
    )


def make_email_html(form: Dict):
    return f"""\
        <html>
        <head></head>
        <body>
            <p>This is sent from {form['name']}<br>
            Email: {form['email']}<br>
            Phone: {form['phone']}<br>
            Message: {form['message']}
            </p>
        </body>
        </html>
        """


def send_email(form: Dict):
    with GmailSender() as gsender:
        # send to my own gmail account
        my_email = gsender.oauth2.username
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Blog Message from {form['name']}"
        msg["To"] = my_email

        html = make_email_html(form)

        msg.attach(MIMEText(html, "html"))
        gsender.send([my_email], msg.as_string())


def send_email_with_grid(form: Dict):
    html = make_email_html(form)
    with GridSender.from_creds_file(GRID_CREDS) as gs:
        gs.send(None, f"Blog Message from {form['name']}", html)


@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        logger.info("Received post from contact form")
        form = request.form
        logger.info(f"Form received: {form}")
        send_email_with_grid(form)
        return render_template("contact.html", contact_sent=True)
    return render_template("contact.html", contact_sent=False)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/form")
def form():
    return render_template("form.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        return f"So you are {request.form['username']}, {request.form['password']}"
    return "Hello"


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
