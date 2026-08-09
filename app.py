from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

CORS(app)

# ==============================
# DATABASE
# ==============================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///render0x.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==============================
# USER MODEL
# ==============================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(150), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)


# ==============================
# CREATE DATABASE
# ==============================

with app.app_context():
    db.create_all()


# ==============================
# HOME
# ==============================

@app.route("/")
def home():

    return "Render0X Backend is running!"


# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:

        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    hashed_password = generate_password_hash(
        password
    )

    user = User(
        name=name,
        email=email,
        password=hashed_password
    )

    db.session.add(user)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Account created successfully!"
    })


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Please enter your email and password."
        }), 400

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    if not check_password_hash(
        user.password,
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    return jsonify({

        "success": True,

        "message": "Login successful!",

        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }

    })


# ==============================
# RUN
# ==============================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
