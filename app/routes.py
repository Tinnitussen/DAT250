"""Provides all routes for the Social Insecurity application.

This file contains the routes for the application. It is imported by the app package.
It also contains the SQL queries used for communicating with the database.
"""

from pathlib import Path

from flask import flash, redirect, render_template, send_from_directory, url_for, abort, session
from flask_login import login_required, logout_user, current_user

from app import app, sqlite, check_username_password, allowed_file
from app.forms import CommentsForm, FriendsForm, IndexForm, PostForm, ProfileForm
from werkzeug.utils import secure_filename



@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    """Provides the index page for the application.

    It reads the composite IndexForm and based on which form was submitted,
    it either logs the user in or registers a new user.

    If no form was submitted, it simply renders the index page.
    """
    index_form = IndexForm()
    login_form = index_form.login
    register_form = index_form.register
    if login_form.validate_on_submit():
        # Try to log in the user
        print(login_form.username.data)
        print(login_form.password.data)
        if check_username_password(login_form.username.data, login_form.password.data):
            flash("You have been logged in!", category="success")
            return redirect(url_for("stream", username=login_form.username.data))
        else:
            flash("Invalid username or password!", category="warning")

    elif register_form.validate_on_submit():
        # Check if user exists
        user = {
            'username': register_form.username.data,
            'password': register_form.password.data,
            'first_name': register_form.first_name.data,
            'last_name': register_form.last_name.data,
        }
        if sqlite.check_user_exists(user.get('username')):
            flash("User already exists!", category="warning")
            return redirect(url_for("index"))
        flash("User successfully created!", category="success")
        sqlite.insert_user(user)
        return redirect(url_for("index"))

    return render_template("index.html.j2", title="Welcome", form=index_form)

@app.route("/stream/<string:username>", methods=["GET", "POST"])
@login_required
def stream(username: str):
    """Provides the stream page for the application.

    If a form was submitted, it reads the form data and inserts a new post into the database.

    Otherwise, it reads the username from the URL and displays all posts from the user and their friends.
    """
    post_form = PostForm()
    if post_form.validate_on_submit():
        filename = ""
        if post_form.image.data:
            if allowed_file(post_form.image.data.filename):
                filename = secure_filename(post_form.image.data.filename)
                path = Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"] / filename 
                post_form.image.data.save(path)
            else:
                flash("Invalid file type!", category="warning")
                return redirect(url_for("stream", username=username))
        sqlite.insert_post(current_user.get_id(), post_form.content.data, filename)
        return redirect(url_for("stream", username=username))
    stream_user_id = sqlite.query_username(username).get("id")
    posts = sqlite.query_posts(stream_user_id)
    return render_template("stream.html.j2", title="Stream", username=username, form=post_form, posts=posts)

@app.route("/comments/<string:username>/<int:post_id>", methods=["GET", "POST"])
@login_required
def comments(username: str, post_id: int):
    """Provides the comments page for the application.
    If a form was submitted, it reads the form data and inserts a new comment into the database.
    Otherwise, it reads the username and post id from the URL and displays all comments for the post.
    """
    comments_form = CommentsForm()
    if comments_form.validate_on_submit():
        sqlite.insert_comment(post_id, comments_form.comment.data, current_user.get_id())
    post = sqlite.query_post(post_id)
    comments = sqlite.query_comments(post_id)
    return render_template(
        "comments.html.j2", title="Comments", username=username, form=comments_form, post=post, comments=comments
    )

@app.route("/logout")
@login_required
def logout():
    """Logs the user out and redirects them to the index page."""
    logout_user()
    flash("You have been logged out!", category="success")
    return redirect(url_for("index"))

@app.route("/friends/<string:username>", methods=["GET", "POST"])
@login_required
def friends(username: str):
    """Provides the friends page for the application.

    If a form was submitted, it reads the form data and inserts a new friend into the database.

    Otherwise, it reads the username from the URL and displays all friends of the user.
    """
    friends_form = FriendsForm()
    get_user = f"""
        SELECT *
        FROM Users
        WHERE username = '{username}';
        """
    user = sqlite.query(get_user, one=True)

    if friends_form.validate_on_submit():
        get_friend = f"""
            SELECT *
            FROM Users
            WHERE username = '{friends_form.username.data}';
            """
        friend = sqlite.query(get_friend, one=True)
        get_friends = f"""
            SELECT f_id
            FROM Friends
            WHERE u_id = {user["id"]};
            """
        friends = sqlite.query(get_friends)

        if friend is None:
            flash("User does not exist!", category="warning")
        elif friend["id"] == user["id"]:
            flash("You cannot be friends with yourself!", category="warning")
        elif friend["id"] in [friend["f_id"] for friend in friends]:
            flash("You are already friends with this user!", category="warning")
        else:
            insert_friend = f"""
                INSERT INTO Friends (u_id, f_id)
                VALUES ({user["id"]}, {friend["id"]});
                """
            sqlite.query(insert_friend)
            flash("Friend successfully added!", category="success")

    get_friends = f"""
        SELECT *
        FROM Friends AS f JOIN Users as u ON f.f_id = u.id
        WHERE f.u_id = {user["id"]} AND f.f_id != {user["id"]};
        """
    friends = sqlite.query(get_friends)
    return render_template("friends.html.j2", title="Friends", username=username, friends=friends, form=friends_form)

@app.route("/profile/<string:username>", methods=["GET", "POST"])
@login_required
def profile(username: str):
    """Provides the profile page for the application.

    If a form was submitted, it reads the form data and updates the user's profile in the database.

    Otherwise, it reads the username from the URL and displays the user's profile.
    """
    profile_form = ProfileForm()
    user = sqlite.query_userprofile(username)
    if not user.get("id") or not current_user.get_id():
        flash("User does not exist!", category="warning")
        return redirect(url_for("profile", username=username))
    if profile_form.validate_on_submit():
        # Check if the current user is the same as the user whose profile is being updated
        print(current_user.get_id())
        print(user.get("id"))
        if current_user.get_id() != user.get("id"):
            flash("You cannot update another user's profile!", category="warning")
            return redirect(url_for("profile", username=username))
        update_profile = f"""
            UPDATE Users
            SET education='{profile_form.education.data}', employment='{profile_form.employment.data}',
                music='{profile_form.music.data}', movie='{profile_form.movie.data}',
                nationality='{profile_form.nationality.data}', birthday='{profile_form.birthday.data}'
            WHERE username='{username}';
            """
        sqlite.query(update_profile)
        return redirect(url_for("profile", username=username))

    return render_template("profile.html.j2", title="Profile", username=username, user=user, form=profile_form)

@app.route("/uploads/<string:filename>")
@login_required
def uploads(filename):
    """Provides an endpoint for serving uploaded files."""
    return send_from_directory(Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"], filename)
