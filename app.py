import os
import re

from flask import Flask, request, jsonify, session, redirect, send_file
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ============================================================
# FLASK SESSION
# ============================================================

app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing")


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing")

if not SUPABASE_PUBLISHABLE_KEY:
    raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is missing")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY is missing")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)

admin_supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# ============================================================
# USERNAME
# ============================================================

def valid_username(username):

    return re.fullmatch(
        r"[A-Za-z0-9_]{3,20}",
        username
    ) is not None


def username_to_email(username):

    username = username.lower().strip()

    return f"{username}@users.render0x.local"


# ============================================================
# HTML PAGES
# ============================================================

@app.route("/")
def index():

    return send_file("index.html")


@app.route("/signin")
def signin_page():

    if session.get("access_token"):
        return redirect("/chat")

    return send_file("signin.html")


@app.route("/signup")
def signup_page():

    if session.get("access_token"):
        return redirect("/chat")

    return send_file("signup.html")


@app.route("/chat")
def chat_page():

    access_token = session.get("access_token")

    # Not signed in = NO CHAT
    if not access_token:
        return redirect("/signin")

    try:

        response = supabase.auth.get_user(access_token)

        if not response or not response.user:

            session.clear()

            return redirect("/signin")

    except Exception as error:

        print("CHAT AUTH ERROR:", error)

        session.clear()

        return redirect("/signin")

    return send_file("chat.html")


@app.route("/about")
def about_page():

    return send_file("about.html")


@app.route("/info")
def info_page():

    return send_file("info.html")


@app.route("/how-to-use")
def how_to_use_page():

    return send_file("how-to-use.html")


# ============================================================
# SIGN UP
# ============================================================

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


    if not valid_username(username):

        return jsonify({
            "success": False,
            "message":
                "Username must be 3-20 characters and use only letters, numbers or _."
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Password must be at least 6 characters."
        }), 400


    email = username_to_email(username)


    try:

        response = admin_supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "username": username
            }
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

        print("SIGNUP ERROR:", error)

        return jsonify({
            "success": False,
            "message":
                "Username may already be registered."
        }), 400


# ============================================================
# SIGN IN
# ============================================================

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


    email = username_to_email(username)


    try:

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })


        if not response.session:

            return jsonify({
                "success": False,
                "message": "Invalid username or password."
            }), 401


        session["access_token"] = \
            response.session.access_token

        session["refresh_token"] = \
            response.session.refresh_token

        session["username"] = username

        session.permanent = True


        return jsonify({
            "success": True,
            "username": username
        })


    except Exception as error:

        print("SIGNIN ERROR:", error)

        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401


# ============================================================
# CURRENT USER
# ============================================================

@app.route("/api/me")
def current_user():

    access_token = session.get("access_token")

    if not access_token:

        return jsonify({
            "signed_in": False
        })


    try:

        response = supabase.auth.get_user(
            access_token
        )


        if not response or not response.user:

            session.clear()

            return jsonify({
                "signed_in": False
            })


        username = session.get("username")


        # Backup: get username from Supabase metadata
        if not username:

            username = response.user.user_metadata.get(
                "username"
            )


        return jsonify({
            "signed_in": True,
            "username": username
        })


    except Exception as error:

        print("ME ERROR:", error)

        session.clear()

        return jsonify({
            "signed_in": False
        })


# ============================================================
# LOGOUT
# ============================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    access_token = session.get("access_token")


    try:

        if access_token:

            # Sign out the Supabase session
            supabase.auth.sign_out()


    except Exception as error:

        print("LOGOUT ERROR:", error)


    finally:

        # Destroy Flask login session
        session.clear()


    return jsonify({
        "success": True
    })


# ============================================================
# CHAT API
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    access_token = session.get("access_token")


    if not access_token:

        return jsonify({
            "success": False,
            "message": "You must sign in first."
        }), 401


    try:

        user_response = supabase.auth.get_user(
            access_token
        )


        if not user_response or not user_response.user:

            session.clear()

            return jsonify({
                "success": False,
                "message":
                    "Your session has expired. Please sign in again."
            }), 401


    except Exception:

        session.clear()

        return jsonify({
            "success": False,
            "message":
                "Your session has expired. Please sign in again."
        }), 401


    data = request.get_json(
        silent=True
    ) or {}


    message = str(
        data.get("message", "")
    ).strip()


    if not message:

        return jsonify({
            "success": False,
            "message": "Message cannot be empty."
        }), 400


    # ========================================================
    # YOUR REAL AI CHAT LOGIC GOES HERE
    # ========================================================

    return jsonify({
        "success": True,
        "reply":
            "Authentication is working. Connect your AI backend here.",
        "username":
            session.get("username")
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", 5000)
        ),
        debug=True
    )
