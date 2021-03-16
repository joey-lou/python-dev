import logging
import os

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

APP_NAME = "auth_tutorial"
ROOT_PATH = os.path.dirname(__file__)
logger = logging.getLogger(APP_NAME)

app = Flask(APP_NAME, root_path=ROOT_PATH)
app.config["SECRET_KEY"] = "ABC"
app.config["UPLOAD_FOLDER"] = f"{ROOT_PATH}/static/files"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{ROOT_PATH}/users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        form = request.form
        logger.info(f"Form received: {form}")
        raw_pwd = form["password"]
        hashed_pwd = generate_password_hash(
            raw_pwd, method="pbkdf2:sha256", salt_length=8
        )
        new_user = User(name=form["name"], email=form["email"], password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        logger.info(f"New user {new_user.name} added with id {new_user.id}")
        return redirect(url_for("secrets"))
    return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        form = request.form
        logger.info(f"Form received: {form}")
        existing_user = User.query.filter_by(email=form["email"]).first_or_404()
        raw_pwd = form["password"]
        if check_password_hash(existing_user.password, raw_pwd):
            login_user(existing_user)
            flash("Logged in successfully.")
            logger.info(
                f"User {existing_user.email} with id {existing_user.id} is logged in!"
            )
            return redirect(url_for("secrets"))
        else:
            return render_template("login.html", fail_login=True)
    return render_template("login.html", fail_login=False)


@app.route("/secrets")
@login_required
def secrets():
    return render_template("secrets.html", current_user=current_user)


@app.route("/downloads/<path:filename>")
@login_required
def download_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"], filename, as_attachment=False
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    app.run(debug=True)
