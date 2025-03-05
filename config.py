import os
import logging
from datetime import timedelta

# Define the base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """Base configuration with common settings."""

    # Use environment variable for security, with fallback
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-never-or-later-maybe")

    # Determine the environment
    ENV = os.environ.get("ENVIRONMENT", "prod")

    # Database configuration (SQLite default)
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )

    # Upload settings
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    ALLOWED_EXTENSIONS = {"xml", "qif", "txt", "stp"}
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB limit

    # Ensure the upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development-specific settings."""

    ENV = "development"
    DEBUG = True
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    # LOG_LEVEL = logging.DEBUG  # More detailed logging


class TestingConfig(Config):
    """Testing-specific settings."""

    ENV = "testing"
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory database for tests
    # LOG_LEVEL = logging.WARNING  # Reduce logging noise in tests


class ProductionConfig(Config):
    """Production-specific settings."""

    ENV = "production"
    DEBUG = False
    # LOG_LEVEL = logging.ERROR  # Only log critical issues
