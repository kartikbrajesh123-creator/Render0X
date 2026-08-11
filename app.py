import os
import re
import sqlite3
from functools import wraps
from flask import Flask, request, jsonify, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# =========================
# FLASK SESSION
# =========================

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "render0x-development-secret-change-this"
)

# =========================
# DATABASE
# =========================

DATABASE = "users.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# USERNAME VALIDATION
# =========================

def valid_username(username):
    return re.fullmatch(
        r"[A-Za-z0-9_]{3,20}",
        username
    ) is not None


# =========================
# HOME
# =========================

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# =========================
# SIGN UP PAGE
# =========================

@app.route("/signup")
def signup_page():

    if session.get("username"):
        return redirect("/")

    return send_from_directory(".", "signup.html")


# =========================
# SIGN UP API
# =========================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    # Username check

    if not valid_username(username):
        return jsonify({
            "success": False,
            "message": "Username must be 3-20 characters and use only letters, numbers or _."
        }), 400

    # Password check

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username.lower(),)
    ).fetchone()

    if existing:

        conn.close()

        return jsonify({
            "success": False,
            "message": "Username already exists."
        }), 409

    # Hash password before storing it

    password_hash = generate_password_hash(password)

    conn.execute(
        """
        INSERT INTO users (username, password)
        VALUES (?, ?)
        """,
        (
            username.lower(),
            password_hash
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully."
    })


# =========================
# SIGN IN PAGE
# =========================

@app.route("/signin")
def signin_page():

    if session.get("username"):
        return redirect("/")

    return send_from_directory(".", "signin.html")


# =========================
# SIGN IN API
# =========================

@app.route("/api/signin", methods=["POST"])
def signin():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    username = str(
        data.get("username", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    conn = get_db()

    user = conn.execute(
        """
        SELECT * FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    conn.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    if not check_password_hash(
        user["password"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    # Login successful

    session.clear()

    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "username": user["username"]
    })


# =========================
# CURRENT USER
# =========================

@app.route("/api/me")
def current_user():

    username = session.get("username")

    if not username:

        return jsonify({
            "signed_in": False
        })

    return jsonify({
        "signed_in": True,
        "username": username
    })


# =========================
# LOGOUT
# =========================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


# =========================
# CHAT PAGE
# =========================

@app.route("/chat")
def chat_page():

    username = session.get("username")

    # Not signed in → cannot open chat

    if not username:
        return redirect("/signin")

    return send_from_directory(".", "chat.html")


# =========================
# CHAT API
# =========================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    username = session.get("username")

    # Protect chat API

    if not username:
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "success": False,
            "message": "Message cannot be empty."
        }), 400

    # =========================
    # YOUR AI CHAT LOGIC HERE
    # =========================

    return jsonify({
        "success": True,
        "reply": "Hello " + username + "! Your login is working.",
        "username": username
    })


# =========================
# RUN
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", 5000)
        ),
        debug=True
    )
