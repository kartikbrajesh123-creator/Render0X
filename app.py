import os
import re
import sqlite3

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# =========================================================
# FLASK SESSION
# =========================================================

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "render0x-development-secret-change-this"
)

# =========================================================
# DATABASE
# =========================================================

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


# =========================================================
# USERNAME VALIDATION
# =========================================================

def valid_username(username):
    return re.fullmatch(
        r"[A-Za-z0-9_]{3,20}",
        username
    ) is not None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# SIGN UP PAGE
# =========================================================

@app.route("/signup")
def signup_page():

    if session.get("username"):
        return redirect(url_for("chat_page"))

    return render_template("signup.html")


# =========================================================
# SIGN UP API
# =========================================================

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

    confirm_password = str(
        data.get("confirm_password", "")
    )

    # Username
    if not valid_username(username):
        return jsonify({
            "success": False,
            "message": "Username must be 3-20 characters and contain only letters, numbers or _."
        }), 400

    # Password
    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400

    # Confirm password
    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400

    conn = get_db()

    try:

        # Check existing username
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username.lower(),)
        ).fetchone()

        if existing:
            return jsonify({
                "success": False,
                "message": "Username already exists."
            }), 409

        # Hash password
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

        return jsonify({
            "success": True,
            "message": "Account created successfully."
        })

    except Exception as error:

        print("SIGNUP ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Could not create account."
        }), 500

    finally:
        conn.close()


# =========================================================
# SIGN IN PAGE
# =========================================================

@app.route("/signin")
def signin_page():

    if session.get("username"):
        return redirect(url_for("chat_page"))

    return render_template("signin.html")


# =========================================================
# SIGN IN API
# =========================================================

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

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Please enter username and password."
        }), 400

    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

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

        # Create Flask login session
        session["username"] = user["username"]
        session.permanent = True

        return jsonify({
            "success": True,
            "username": user["username"]
        })

    except Exception as error:

        print("SIGNIN ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Could not sign in."
        }), 500

    finally:
        conn.close()


# =========================================================
# CURRENT USER
# =========================================================

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


# =========================================================
# CHAT PAGE
# =========================================================

@app.route("/chat")
def chat_page():

    username = session.get("username")

    if not username:
        return redirect(url_for("signin_page"))

    return render_template(
        "chat.html",
        username=username
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


# =========================================================
# CHAT API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    username = session.get("username")

    if not username:

        return jsonify({
            "success": False,
            "message": "You must sign in first."
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

    # -----------------------------------------------------
    # YOUR REAL AI/CHAT LOGIC GOES HERE
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "reply": "Your message was received.",
        "username": username
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )
