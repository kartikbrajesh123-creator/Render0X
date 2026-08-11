import os
import json
import hashlib
import secrets

from flask import Flask, render_template, request, jsonify, session, redirect


app = Flask(__name__)

# =========================================================
# FLASK SESSION
# =========================================================

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "render0x-development-secret-change-this"
)


# =========================================================
# USER DATABASE
# =========================================================

USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return salt, password_hash


def check_password(password, salt, stored_hash):

    _, password_hash = hash_password(password, salt)

    return secrets.compare_digest(
        password_hash,
        stored_hash
    )


# =========================================================
# USERNAME VALIDATION
# =========================================================

def valid_username(username):

    if not 3 <= len(username) <= 20:
        return False

    return all(
        character.isalnum() or character == "_"
        for character in username
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# SIGN UP PAGE
# =========================================================

@app.route("/signup")
def signup_page():

    if session.get("username"):
        return redirect("/chat")

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

    # -----------------------------
    # Validate username
    # -----------------------------

    if not valid_username(username):

        return jsonify({
            "success": False,
            "message":
                "Username must be 3-20 characters and contain only letters, numbers or _."
        }), 400

    # -----------------------------
    # Validate password
    # -----------------------------

    if len(password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Password must be at least 6 characters."
        }), 400

    # -----------------------------
    # Load users
    # -----------------------------

    users = load_users()

    username_key = username.lower()

    # -----------------------------
    # Check existing account
    # -----------------------------

    if username_key in users:

        return jsonify({
            "success": False,
            "message":
                "Username already exists."
        }), 409

    # -----------------------------
    # Hash password
    # -----------------------------

    salt, password_hash = hash_password(password)

    # -----------------------------
    # Create account
    # -----------------------------

    users[username_key] = {

        "username": username,

        "salt": salt,

        "password_hash": password_hash

    }

    save_users(users)

    # -----------------------------
    # Automatically sign user in
    # -----------------------------

    session.clear()

    session["username"] = username

    return jsonify({
        "success": True,
        "username": username
    })


# =========================================================
# SIGN IN PAGE
# =========================================================

@app.route("/signin")
def signin_page():

    if session.get("username"):
        return redirect("/chat")

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
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not username or not password:

        return jsonify({
            "success": False,
            "message":
                "Please enter username and password."
        }), 400

    users = load_users()

    username_key = username.lower()

    user = users.get(username_key)

    # -----------------------------
    # User doesn't exist
    # -----------------------------

    if not user:

        return jsonify({
            "success": False,
            "message":
                "Invalid username or password."
        }), 401

    # -----------------------------
    # Check password
    # -----------------------------

    if not check_password(
        password,
        user["salt"],
        user["password_hash"]
    ):

        return jsonify({
            "success": False,
            "message":
                "Invalid username or password."
        }), 401

    # -----------------------------
    # Create Flask session
    # -----------------------------

    session.clear()

    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "username": user["username"]
    })


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

    # ---------------------------------
    # NOT SIGNED IN = NO CHAT
    # ---------------------------------

    if not username:
        return redirect("/signin")

    return render_template(
        "chat.html",
        username=username
    )


# =========================================================
# CHAT API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    username = session.get("username")

    # ---------------------------------
    # Protect API
    # ---------------------------------

    if not username:

        return jsonify({
            "success": False,
            "message":
                "You must sign in first."
        }), 401

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "success": False,
            "message":
                "Message cannot be empty."
        }), 400

    # ---------------------------------
    # TEMPORARY CHAT RESPONSE
    # ---------------------------------
    #
    # Replace this section later
    # with your real AI/chat system.
    #

    return jsonify({
        "success": True,
        "username": username,
        "reply":
            "Your login is working! "
            "Now connect your real chat/AI backend here."
    })


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
# SIMPLE PAGES
# =========================================================

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/info")
def info():
    return render_template("info.html")


@app.route("/how-to-use")
def how_to_use():
    return render_template("how-to-use.html")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", 5000)
        ),
        debug=True
    )
