from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

CORS(app)


# ==============================
# DATABASE
# ==============================

DATABASE = "render0x.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_database()


# ==============================
# HOME
# ==============================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "Render0X Backend is running!"
    })


# ==============================
# SIGN UP
# ==============================

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400


    password_hash = generate_password_hash(password)


    try:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO users
            (username, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, password_hash)
        )

        conn.commit()
        conn.close()


        return jsonify({
            "success": True,
            "message": "Account created successfully!"
        })


    except sqlite3.IntegrityError:

        return jsonify({
            "success": False,
            "message": "Username or email already exists."
        }), 409


# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email", "").strip()
    password = data.get("password", "")


    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Please enter your email and password."
        }), 400


    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    conn.close()


    if user is None:

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


    return jsonify({
        "success": True,
        "message": "Login successful!",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    })


# ==============================
# START SERVER
# ==============================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
