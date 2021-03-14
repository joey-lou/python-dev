import datetime as dt
import logging
import os

from flask import Flask, redirect, render_template
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email

from daily.day67.utils import ContactForm, PostForm, send_email_with_grid

ROOT_PATH = os.path.dirname(__file__)
STATIC_PATH = os.path.join(ROOT_PATH, "../day59/static")  # share same static files
TEMPLATE_PATH = os.path.join(ROOT_PATH, "templates")

APP_NAME = "personal_blog_site"
app = Flask(APP_NAME, static_folder=STATIC_PATH, template_folder=TEMPLATE_PATH)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{ROOT_PATH}/posts.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

ckeditor = CKEditor(app)
db = SQLAlchemy(app)
Bootstrap(app)
app.secret_key = "ABC"
logger = logging.getLogger(APP_NAME)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[Email()])
    password = PasswordField(
        label="Password", validators=[DataRequired(message="Please enter password")]
    )
    submit = SubmitField(label="Login")


@app.route("/")
def home():
    blogs = BlogPost.query.all()
    return render_template("index.html", date=dt.date.today(), blogs=blogs)


@app.route("/about")
def about():
    return render_template("about.html")


# ~~~~~~~ blog end-points ~~~~~~~~ #
@app.route("/blogs/<int:blog_id>")
def blog_post(blog_id):
    blog = BlogPost.query.filter_by(id=blog_id).first()
    return render_template("post.html", blog=blog, date=dt.date.today())


@app.route("/new-blog/", methods=["POST", "GET"])
def new_blog_post():
    form = PostForm()
    if form.validate_on_submit():
        new_blog = BlogPost(
            date=dt.date.today().strftime("%B %d, %Y"), **form.to_dict()
        )
        db.session.add(new_blog)
        db.session.commit()
        logger.info(f"successfully added blog with id {new_blog.id}")
        return redirect("/")
    return render_template("make-post.html", form=form)


@app.route("/edit-blog/<int:blog_id>", methods=["POST", "GET"])
def edit_blog_post(blog_id):
    old_blog = BlogPost.query.get(blog_id)
    form = PostForm(
        title=old_blog.title,
        subtitle=old_blog.subtitle,
        author=old_blog.author,
        img_url=old_blog.img_url,
        body=old_blog.body,
    )
    if form.validate_on_submit():
        new_blog = BlogPost(
            id=old_blog.id, date=dt.date.today().strftime("%B %d, %Y"), **form.to_dict()
        )
        db.session.delete(old_blog)
        db.session.add(new_blog)
        db.session.commit()
        logger.info(f"successfully updated blog with id {new_blog.id}")
        return redirect("/")
    return render_template("make-post.html", form=form)


@app.route("/delete-blog/<int:blog_id>", methods=["GET"])
def delete_blog_post(blog_id):
    old_blog = BlogPost.query.get(blog_id)
    db.session.delete(old_blog)
    db.session.commit()
    logger.info(f"successfully deleted blog with id {old_blog.id}")
    return redirect("/")


# ~~~~~~~ user end-points ~~~~~~~~ #
@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    # in addition to checking request method, it validates fields entered in form posted
    if form.validate_on_submit():
        return render_template(
            "login.html", form=form, is_logged_in=True, email=form.email.data
        )
    return render_template("login.html", form=form, is_logged_in=False)


@app.route("/contact", methods=["POST", "GET"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        logger.info("Received post from contact form")
        logger.info(f"Form received: {form}")
        send_email_with_grid(form)
        return redirect("/")
    return render_template("contact.html", form=form, contact_sent=False)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    app.run(debug=True)
