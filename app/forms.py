"""Provides all forms used in the Social Insecurity application.

This file is used to define all forms used in the application.
It is imported by the app package.

Example:
    from flask import Flask
    from app.forms import LoginForm

    app = Flask(__name__)

    # Use the form
    form = LoginForm()
    if form.validate_on_submit() and form.login.submit.data:
        username = form.username.data
    """

from datetime import datetime
from typing import cast
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    FileField,
    FormField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    Optional,
)
# Defines all forms in the application, these will be instantiated by the template,
# and the routes.py will read the values of the fields

class LoginForm(FlaskForm):
    """Provides the login form for the application."""
    username = StringField(label="Username", render_kw={"placeholder": "Username"}, validators=[DataRequired(), Length(1, 64)]) 
    password = PasswordField(label="Password", render_kw={"placeholder": "Password"}, validators=[DataRequired(), Length(8, 99)])
    remember_me = BooleanField(
        label="Remember me"
    )  # TODO: It would be nice to have this feature implemented, probably by using cookies
    submit = SubmitField(label="Sign In", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    """Provides the registration form for the application."""

    first_name = StringField(label="First Name", render_kw={"placeholder": "First Name"}, validators=[Optional(), Length(1, 64), DataRequired()])
    last_name = StringField(label="Last Name", render_kw={"placeholder": "Last Name"}, validators=[Optional(), Length(1, 64), DataRequired()])
    username = StringField(label="Username", render_kw={"placeholder": "Username"}, validators=[Length(1, 64), DataRequired()])
    password = PasswordField(label="Password", render_kw={"placeholder": "Password"}, validators=[Length(8, 99), DataRequired(), EqualTo("confirm_password")])
    confirm_password = PasswordField(label="Confirm Password", render_kw={"placeholder": "Confirm Password"}, validators=[DataRequired()])
    submit = SubmitField(label="Sign Up", validators=[DataRequired()])


class IndexForm(FlaskForm):
    """Provides the composite form for the index page."""

    login = cast(LoginForm, FormField(LoginForm))
    register = cast(RegisterForm, FormField(RegisterForm))


class PostForm(FlaskForm):
    """Provides the post form for the application."""

    content = TextAreaField(label="New Post", render_kw={"placeholder": "What are you thinking about?"}, validators=[Length(1,500), DataRequired()])
    image = FileField(label="Image", validators=[Optional()])
    submit = SubmitField(label="Post", validators=[DataRequired()])


class CommentsForm(FlaskForm):
    """Provides the comment form for the application."""

    comment = TextAreaField(label="New Comment", render_kw={"placeholder": "What do you have to say?"}, validators=[Length(1, 500), DataRequired()])
    submit = SubmitField(label="Comment", validators=[DataRequired()])


class FriendsForm(FlaskForm):
    """Provides the friend form for the application."""

    username = StringField(label="Friend's username", render_kw={"placeholder": "Username"}, validators=[Length(1, 64), DataRequired()])
    submit = SubmitField(label="Add Friend", validators=[DataRequired()])


class ProfileForm(FlaskForm):
    """Provides the profile form for the application."""

    education = StringField(label="Education", render_kw={"placeholder": "Highest education"}, validators=[Optional(), Length(1, 64)])
    employment = StringField(label="Employment", render_kw={"placeholder": "Current employment"}, validators=[Optional(), Length(1, 64)])
    music = StringField(label="Favorite song", render_kw={"placeholder": "Favorite song"}, validators=[Optional(), Length(1, 64)])
    movie = StringField(label="Favorite movie", render_kw={"placeholder": "Favorite movie"}, validators=[Optional(), Length(1, 64)])
    nationality = StringField(label="Nationality", render_kw={"placeholder": "Your nationality"}, validators=[Optional(), Length(1, 64)])
    birthday = DateField(label="Birthday", default=datetime.now(), validators=[Optional()])
    submit = SubmitField(label="Update Profile", validators=[DataRequired()])
