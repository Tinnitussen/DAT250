"""Provides the configuration for the Social Insecurity application.

This file is used to set the configuration for the application.

Example:
    from flask import Flask
    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # Use the configuration
    secret_key = app.config["SECRET_KEY"]
"""

import os
from dotenv import load_dotenv
load_dotenv('.env.local')
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLITE3_DATABASE_PATH = "sqlite3.db"  # Path relative to the Flask instance folder
    UPLOADS_FOLDER_PATH = "uploads"  # Path relative to the Flask instance folder
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'} # Allowed file extensions for uploads
    SESSION_COOKIE_SAMESITE = 'Strict' # Prevents CSRF attacks