import os
import re

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# =========================================================
# FLASK SESSION
# =========================================================

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing")


# =========================================================
# SUPABASE
# =========================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing")

if not SUPABASE_PUBLISHABLE_KEY:
    raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is missing")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY is missing")


# Normal user client
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)

# Admin client
# NEVER put the secret key in HTML or JavaScript.
admin_supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# =========================================================
# USERNAME HELPERS
# =========================================================

def valid_username(username):
    """
    Username:
    3-20 characters
    letters, numbers and underscore only
    """
    return re.fullmatch(r"[A-Za-z0-9_]{3,20}", username) is not None


def username_to_email(username):
    """
    Supabase uses an internal email address.
    The user only sees their username.
    """
    username = username.lower().strip()

    return f"{username}@users.render0x.local"


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# SIGN IN PAGE
# =========================================================

@app.route("/signin")
def signin_page():

    # Already signed in
    if session.get("access_token"):
        return redirect(url_for("chat_page"))

    return render_template("signin.html")


# =========================================================
# SIGN UP PAGE
# =========================================================

@app.route("/signup")
def signup_page():

    # Already signed in
    if session.get("access_token"):
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

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    # Check username
    if not valid_username(username):
        return jsonify({
            "success": False,
            "message": "Username must be 3-20 characters and contain only letters, numbers or _."
        }), 400

    # Check password
    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400

    internal_email = username_to_email(username)

    try:

        # Create account in Supabase
        response = admin_supabase.auth.admin.create_user({
            "email": internal_email,
            "password": password,
            "email_confirm": True
        })

        if not response.user:
            return jsonify({
                "success": False,
                "message": "Could not create account."
            }), 400

        return jsonify({
            "success": True,
            "message": "Account created successfully."
        })

    except Exception as error:

        print("SIGN UP ERROR:", error)

        error_text = str(error).lower()

        if "already" in error_text or "exists" in error_text or "duplicate" in error_text:
            return jsonify({
                "success": False,
                "message": "Username already exists."
            }), 409

        return jsonify({
            "success": False,
            "message": "Could not create account. Please try again."
        }), 400


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

    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not valid_username(username):
        return jsonify({
            "success": False,
            "message": "Invalid username."
        }), 400

    if not password:
        return jsonify({
            "success": False,
            "message": "Please enter your password."
        }), 400

    internal_email = username_to_email(username)

    try:

        response = supabase.auth.sign_in_with_password({
            "email": internal_email,
            "password": password
        })

        if not response.session:
            return jsonify({
                "success": False,
                "message": "Invalid username or password."
            }), 401

        # Save login session
        session["access_token"] = response.session.access_token
        session["refresh_token"] = response.session.refresh_token
        session["username"] = username

        session.permanent = True

        return jsonify({
            "success": True,
            "username": username
        })

    except Exception as error:

        print("SIGN IN ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/me")
def current_user():

    access_token = session.get("access_token")

    if not access_token:
        return jsonify({
            "signed_in": False
        })

    try:

        response = supabase.auth.get_user(access_token)

        if not response or not response.user:
            session.clear()

            return jsonify({
                "signed_in": False
            })

        return jsonify({
            "signed_in": True,
            "username": session.get("username")
        })

    except Exception:

        session.clear()

        return jsonify({
            "signed_in": False
        })


# =========================================================
# CHAT PAGE
# =========================================================

@app.route("/chat")
def chat_page():

    access_token = session.get("access_token")

    # Not signed in = cannot open chat
    if not access_token:
        return redirect(url_for("signin_page"))

    try:

        response = supabase.auth.get_user(access_token)

        if not response or not response.user:
            session.clear()
            return redirect(url_for("signin_page"))

    except Exception:

        session.clear()
        return redirect(url_for("signin_page"))

    return render_template(
        "chat.html",
        username=session.get("username")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    # Destroy our website login session
    session.clear()

    return jsonify({
        "success": True
    })


# =========================================================
# PROTECTED CHAT API
# =========================================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    access_token = session.get("access_token")

    if not access_token:
        return jsonify({
            "success": False,
            "message": "You must sign in first."
        }), 401

    try:

        user_response = supabase.auth.get_user(access_token)

        if not user_response or not user_response.user:

            session.clear()

            return jsonify({
                "success": False,
                "message": "Your session has expired. Please sign in again."
            }), 401

    except Exception:

        session.clear()

        return jsonify({
            "success": False,
            "message": "Your session has expired. Please sign in again."
        }), 401

    data = request.get_json(silent=True) or {}

    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "success": False,
            "message": "Message cannot be empty."
        }), 400

    # =====================================================
    # PUT YOUR REAL AI CHAT LOGIC HERE
    # =====================================================

    return jsonify({
        "success": True,
        "reply": "Authentication is working. Connect your AI backend here.",
        "username": session.get("username")
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
