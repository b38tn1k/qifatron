import requests
import datetime
from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    abort
)

digital_pipelines_bp = Blueprint("digital_pipelines", __name__)

@digital_pipelines_bp.route("/")
def test():
    return render_template("digital_pipelines/digital_pipelines.html", title="Digital Pipelines")
