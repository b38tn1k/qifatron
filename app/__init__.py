from flask import Flask, redirect, url_for

from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app.routes import testing_bp, qif_bp, digital_pipelines_bp

app.register_blueprint(qif_bp, url_prefix="/qif")
app.register_blueprint(digital_pipelines_bp, url_prefix="/digital_pipelines")


from app import routes, models

@app.route("/")
def index():
    return redirect(url_for("qif.start"))  # Correct blueprint endpoint