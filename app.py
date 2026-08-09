 
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

# Secret key required for Flask sessions
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "render0x-development-secret"
)


# =====================================================
# CORS
# =====================================================

CORS(
    app,
    supports_credentials=True,
    origins=[
        "https://render0x.onrender.com"
    ]
)


# =====================================================
# SESSION COOKIE SETTINGS
# =====================================================

app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"


# =====================================================
# DATABASE
# =====================================================

DATABASE = "render0x.db"


def get_db():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def init_db():

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()

    connection.close()


init_db()


# =====================================================
# HOME
# =====================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "Render0X Backend is running!"
    })


# =====================================================
# SIGN UP
# =====================================================

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400


    name = data.get("name", "").strip()

    email = data.get("email", "").strip().lower()

    password = data.get("password", "")


    if not name or not email or not password:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters."
        }), 400


    connection = get_db()


    existing_user = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()


    if existing_user:

        connection.close()

        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409


    hashed_password = generate_password_hash(password)


    connection.execute(
        """
        INSERT INTO users (name, email, password)
        VALUES (?, ?, ?)
        """,
        (
            name,
            email,
            hashed_password
        )
    )


    connection.commit()

    connection.close()


    return jsonify({
        "success": True,
        "message": "Account created successfully!"
    })


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400


    email = data.get("email", "").strip().lower()

    password = data.get("password", "")


    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Please enter your email and password."
        }), 400


    connection = get_db()


    user = connection.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()


    connection.close()


    if not user:

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401


    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401


    # =================================================
    # CREATE LOGIN SESSION
    # =================================================

    session.clear()

    session["user_id"] = user["id"]

    session["user_name"] = user["name"]

    session["user_email"] = user["email"]


    return jsonify({

        "success": True,

        "message": "Login successful!",

        "user": {

            "id": user["id"],

            "name": user["name"],

            "email": user["email"]

        }

    })


# =====================================================
# CHECK CURRENT LOGIN
# =====================================================

@app.route("/me", methods=["GET"])
def me():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Not logged in."
        }), 401


    return jsonify({

        "success": True,

        "user": {

            "id": session["user_id"],

            "name": session["user_name"],

            "email": session["user_email"]

        }

    })


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({

        "success": True,

        "message": "Logged out successfully."

    })


# =====================================================
# START SERVER
# =====================================================

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
 
