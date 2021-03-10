import logging
import os
import random

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

APP_NAME = "cafe"
logger = logging.getLogger(APP_NAME)

##Connect to Database
ROOT_PATH = os.path.dirname(__file__)
API_KEY_ALLOWED = ["abc", "bar"]
app = Flask(APP_NAME, root_path=ROOT_PATH)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{ROOT_PATH}/cafes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


##Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return f"Cafe {self.id} {self.name}"

    def to_serializable(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


@app.route("/")
def home():
    return render_template("index.html")


## HTTP GET - Read Record
@app.route("/random")
def get_random():
    all_cafes = Cafe.query.all()
    return jsonify(random.choice(all_cafes).to_serializable())


@app.route("/all")
def get_all():
    all_cafes = Cafe.query.all()
    return jsonify(cafes=[c.to_serializable() for c in all_cafes])


@app.route("/search")
def search():
    kwargs = {
        "name": request.args.get("name"),
        "location": request.args.get("loc"),
        "id": request.args.get("id"),
    }
    query = Cafe.query.filter_by(**{k: v for k, v in kwargs.items() if v})
    logger.info(f"Querying using {query}")
    cafes = query.all()
    if cafes:
        return jsonify(cafes=[c.to_serializable() for c in cafes]), 200
    else:
        return jsonify(error="Cafe not found."), 404


## HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(success="Successfully added the new cafe."), 200


## HTTP PUT/PATCH - Update Record
@app.route("/update-name/<int:id>/<new_name>", methods=["PATCH"])
def update_name(id, new_name):
    cafe = Cafe.query.filter_by(id=id).first()
    if not cafe:
        return jsonify(error="Cafe not found."), 404
    cafe.name = new_name
    db.session.commit()
    return jsonify(success=f"Successfully modified cafe name for {id}."), 200


@app.route("/report-closed/<int:id>", methods=["DELETE"])
def remove_cafe(id):
    api_key = request.args.get("api")
    if api_key not in API_KEY_ALLOWED:
        return jsonify(error="API not valid."), 403

    cafe = Cafe.query.filter_by(id=id).first()
    if not cafe:
        return jsonify(error="Cafe not found."), 404
    db.session.delete(cafe)
    db.session.commit()
    return jsonify(success=f"Successfully modified cafe name for {id}."), 200


## HTTP DELETE - Delete Record


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    app.run(debug=True)
