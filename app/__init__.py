"""Provides the app package for the Social Insecurity application. The package contains the Flask app and all of the extensions and routes."""

from pathlib import Path
from typing import cast

from flask import Flask, flash, redirect, url_for

from app.config import Config
from app.database import SQLite3

from flask_login import LoginManager, UserMixin, login_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

# Instantiate and configure the app
app = Flask(__name__)
bcrypt = Bcrypt(app)
csfr = CSRFProtect(app)
app.config.from_object(Config)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    """
    Provides the User class for the application.
    This class is used by the flask_login package to manage user sessions.
    """
    def __init__(self, user_id, username, first_name='', last_name=''):
        self.id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
    @staticmethod
    def get(user_id):
        """Returns a User object based on the user id."""
        user = sqlite.query_userid(user_id)
        if user is None:
            return None
        return User(user['id'], user['username'], user['first_name'], user['last_name'])

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    """Redirects the user to the index page if they are not logged in."""
    flash("You must be logged in to view this page!", category="warning")
    return redirect(url_for("index"))


# Helper function for logging in
def check_username_password(username: str, password: str) -> bool:
    """Login helper function"""
    user = sqlite.query_username(username)
    if not user:
        return False
    if username == user["username"] and bcrypt.check_password_hash(user["password"], password):
        return login_user(User(user["id"], user["username"], user["first_name"], user["last_name"]))
    return False


# Helper function for uploading files
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'] 


# Instantiate the sqlite database extension
sqlite = SQLite3(app, schema="schema.sql")

# Create the instance and upload folder if they do not exist
with app.app_context():
    instance_path = Path(app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir(parents=True, exist_ok=True)
    upload_path = instance_path / cast(str, app.config["UPLOADS_FOLDER_PATH"])
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)

# Import the routes after the app is configured
from app import routes  # noqa: E402,F401
