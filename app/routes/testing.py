import requests
import datetime
from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    abort
)
from app.models import GameScore 

testing_bp = Blueprint("testing", __name__)

@testing_bp.route("/")
def test():
    return render_template("testing/game.html", scores=GameScore.get_high_scores())

@testing_bp.route("/add-score", methods=["POST"])
def add_score():
    """Adds a new game score to the database."""
    data = request.get_json()
    if not data or "name" not in data or "score" not in data:
        return jsonify({"error": "Invalid data. 'name' and 'score' are required."}), 400

    name = data["name"]
    score = data["score"]

    if not isinstance(score, int):
        return jsonify({"error": "'score' must be an integer."}), 400

    try:
        GameScore.add_game_score(name=name, score=score)
        return jsonify({"message": "Score added successfully."}), 201
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@testing_bp.route("/get-scores", methods=["GET"])
def get_scores():
    """Fetches the top high scores from the database."""
    try:
        high_scores = GameScore.get_high_scores(limit=10)
        scores = [{"name": score.name, "score": score.score} for score in high_scores]
        return jsonify(scores), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

SHARED_SECRET = "rsigmarsigmarsigmarsigmarsigmarsigmarsigmarsigmarsigma"
EB_URL = "https://www.rsigma.io/arduino"

@testing_bp.route("/calculator", methods=["GET"])
def calculator_form():
    """
    Render the calculator page with no result yet.
    """
    return render_template("testing/calculator.html")

@testing_bp.route("/calculate", methods=["POST"])
def calculate():
    """
    Process the form data, call the EB server's calculator, and show the result.
    """
    try:
        # Extract form fields
        number1 = float(request.form.get("number1", 0))
        number2 = float(request.form.get("number2", 0))
        operation_type = request.form.get("operation", "add")

        # Prepare JSON to send to EB
        data_to_send = {
            "device": "rsigma-local",
            "operation": {
                "type": operation_type,
                "number1": number1,
                "number2": number2
            }
        }

        # Add the shared secret to headers
        headers = {
            "X-Shared-Secret": SHARED_SECRET,
            "Content-Type": "application/json"
        }

        # POST to the EB server
        response = requests.post(EB_URL, headers=headers, json=data_to_send)

        # Handle the EB response
        if response.status_code == 200:
            eb_data = response.json()
            # The EB server returns: {"device":..., "operation":..., "result":...}
            result = eb_data.get("result")
            return render_template("testing/calculator.html", result=result)
        else:
            # Show an error if EB didn't return 200
            error_msg = f"EB error: {response.status_code} - {response.text}"
            return render_template("testing/calculator.html", result=error_msg)
    except Exception as e:
        return render_template("testing/calculator.html", result=f"Error: {str(e)}")