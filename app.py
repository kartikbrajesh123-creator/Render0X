import os
import re

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

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


# Normal Supabase client
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)


# Admin Supabase client
#
# IMPORTANT:
# This secret key must NEVER be placed inside HTML,
# JavaScript, or any frontend file.
#
admin_supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# ============================================================
# USERNAME HELPERS
# ============================================================

def valid_username(username):
    """
    Username rules:

    3-20 characters
    Letters, numbers and underscore only
    """

    return re.fullmatch(
        r"[A-Za-z0-9_]{3,20}",
        username
    ) is not None


def username_to_email(username):
    """
    Supabase password authentication normally uses an email.

    Your users only enter a username.

    We internally convert:

        dev123

    into:

        dev123@users.render0x.local

    The user never needs to see this internal email.
    """

    username = username.lower().strip()

    return f"{username}@users.render0x.local"


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


# ============================================================
# SIGN UP PAGE
# ============================================================

@app.route("/signup")
def signup_page():

    # If already signed in,
    # don't show signup page.
    if session.get("access_token"):

        return redirect(
            url_for("chat_page")
        )

    return render_template("signup.html")


# ============================================================
# SIGN UP API
# ============================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True)


    # --------------------------------------------------------
    # CHECK REQUEST
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # CHECK USERNAME
    # --------------------------------------------------------

    if not valid_username(username):

        return jsonify({
            "success": False,
            "message":
                "Username must be 3-20 characters "
                "and contain only letters, numbers or _."
        }), 400


    # --------------------------------------------------------
    # CHECK PASSWORD
    # --------------------------------------------------------

    if len(password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Password must contain at least 6 characters."
        }), 400


    # Convert username into internal email
    internal_email = username_to_email(username)


    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    try:

        response = admin_supabase.auth.admin.create_user({

            "email": internal_email,

            "password": password,

            # Automatically verify this internal email
            "email_confirm": True

        })


        return jsonify({

            "success": True,

            "username": username

        })


    except Exception as error:

        print(
            "SIGNUP ERROR:",
            error
        )


        error_text = str(error).lower()


        # Username already exists
        if (
            "already" in error_text
            or
            "exists" in error_text
            or
            "duplicate" in error_text
        ):

            return jsonify({

                "success": False,

                "message":
                    "Username already exists."

            }), 409


        return jsonify({

            "success": False,

            "message":
                "Could not create account."

        }), 400


# ============================================================
# SIGN IN PAGE
# ============================================================

@app.route("/signin")
def signin_page():

    # Already signed in?
    if session.get("access_token"):

        return redirect(
            url_for("chat_page")
        )


    return render_template(
        "signin.html"
    )


# ============================================================
# SIGN IN API
# ============================================================

@app.route("/api/signin", methods=["POST"])
def signin():

    data = request.get_json(
        silent=True
    )


    # --------------------------------------------------------
    # CHECK REQUEST
    # --------------------------------------------------------

    if not data:

        return jsonify({

            "success": False,

            "message":
                "Invalid request."

        }), 400


    username = str(
        data.get("username", "")
    ).strip().lower()


    password = str(
        data.get("password", "")
    )


    # --------------------------------------------------------
    # CHECK USERNAME
    # --------------------------------------------------------

    if not valid_username(username):

        return jsonify({

            "success": False,

            "message":
                "Username must be 3-20 characters "
                "and contain only letters, numbers or _."

        }), 400


    # --------------------------------------------------------
    # CHECK PASSWORD
    # --------------------------------------------------------

    if not password:

        return jsonify({

            "success": False,

            "message":
                "Please enter your password."

        }), 400


    # Convert username to internal email
    internal_email = username_to_email(
        username
    )


    # --------------------------------------------------------
    # SIGN IN WITH SUPABASE
    # --------------------------------------------------------

    try:

        response = supabase.auth.sign_in_with_password({

            "email": internal_email,

            "password": password

        })


        # No session = login failed
        if not response.session:

            return jsonify({

                "success": False,

                "message":
                    "Invalid username or password."

            }), 401


        # ----------------------------------------------------
        # SAVE LOGIN SESSION
        # ----------------------------------------------------

        session["access_token"] = (
            response.session.access_token
        )

        session["refresh_token"] = (
            response.session.refresh_token
        )

        session["username"] = username

        session.permanent = True


        return jsonify({

            "success": True,

            "username": username

        })


    except Exception as error:

        print(
            "SIGN IN ERROR:",
            error
        )


        return jsonify({

            "success": False,

            "message":
                "Invalid username or password."

        }), 401


# ============================================================
# CURRENT USER
# ============================================================

@app.route("/api/me")
def current_user():

    access_token = session.get(
        "access_token"
    )


    # --------------------------------------------------------
    # NOT SIGNED IN
    # --------------------------------------------------------

    if not access_token:

        return jsonify({

            "signed_in": False

        })


    # --------------------------------------------------------
    # VERIFY SESSION
    # --------------------------------------------------------

    try:

        response = supabase.auth.get_user(
            access_token
        )


        if (
            not response
            or
            not response.user
        ):

            session.clear()


            return jsonify({

                "signed_in": False

            })


        return jsonify({

            "signed_in": True,

            "username":
                session.get("username")

        })


    except Exception as error:

        print(
            "CURRENT USER ERROR:",
            error
        )


        session.clear()


        return jsonify({

            "signed_in": False

        })


# ============================================================
# CHAT PAGE
# ============================================================

@app.route("/chat")
def chat_page():

    access_token = session.get(
        "access_token"
    )


    # --------------------------------------------------------
    # NO LOGIN = NO CHAT
    # --------------------------------------------------------

    if not access_token:

        return redirect(
            url_for("signin_page")
        )


    # --------------------------------------------------------
    # VERIFY LOGIN WITH SUPABASE
    # --------------------------------------------------------

    try:

        response = supabase.auth.get_user(
            access_token
        )


        if (
            not response
            or
            not response.user
        ):

            session.clear()


            return redirect(
                url_for("signin_page")
            )


    except Exception as error:

        print(
            "CHAT AUTH ERROR:",
            error
        )


        session.clear()


        return redirect(
            url_for("signin_page")
        )


    # --------------------------------------------------------
    # OPEN CHAT
    # --------------------------------------------------------

    return render_template(

        "chat.html",

        username=session.get(
            "username"
        )

    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    access_token = session.get(
        "access_token"
    )


    try:

        if access_token:

            # Sign out from Supabase
            supabase.auth.sign_out()


    except Exception as error:

        print(
            "LOGOUT ERROR:",
            error
        )


    finally:

        # Always destroy Flask session
        session.clear()


    return jsonify({

        "success": True

    })


# ============================================================
# PROTECTED CHAT API
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    access_token = session.get(
        "access_token"
    )


    # --------------------------------------------------------
    # CHECK LOGIN
    # --------------------------------------------------------

    if not access_token:

        return jsonify({

            "success": False,

            "message":
                "You must sign in first."

        }), 401


    # --------------------------------------------------------
    # VERIFY USER
    # --------------------------------------------------------

    try:

        user_response = supabase.auth.get_user(
            access_token
        )


        if (
            not user_response
            or
            not user_response.user
        ):

            session.clear()


            return jsonify({

                "success": False,

                "message":
                    "Your session has expired. "
                    "Please sign in again."

            }), 401


    except Exception as error:

        print(
            "CHAT AUTH ERROR:",
            error
        )


        session.clear()


        return jsonify({

            "success": False,

            "message":
                "Your session has expired. "
                "Please sign in again."

        }), 401


    # --------------------------------------------------------
    # GET MESSAGE
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}


    message = str(
        data.get("message", "")
    ).strip()


    if not message:

        return jsonify({

            "success": False,

            "message":
                "Message cannot be empty."

        }), 400


    # ========================================================
    # YOUR REAL AI CHAT LOGIC GOES HERE
    # ========================================================

    return jsonify({

        "success": True,

        "reply":
            "Your authentication is working. "
            "Connect your chat/AI backend here.",

        "username":
            session.get("username")

    })


# ============================================================
# RUN SERVER
# ============================================================

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
