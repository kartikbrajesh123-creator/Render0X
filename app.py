from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app)


@app.route("/")
def home():
    return "Render0X Backend is running!"


@app.route("/contact", methods=["POST"])
def contact():

    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    print("===== NEW RENDEROX MESSAGE =====")
    print("Name:", name)
    print("Email:", email)
    print("Message:", message)
    print("================================")

    return jsonify({
        "success": True,
        "message": "Your suggestion was received!"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
