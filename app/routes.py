"""Provides all routes for the Social Insecurity application.

This file contains the routes for the application. It is imported by the app package.
It also contains the SQL queries used for communicating with the database.
"""

from pathlib import Path
from flask import flash, redirect, make_response, render_template, send_from_directory, url_for, session
from flask_login import login_required, logout_user, current_user
from app import app, sqlite, bcrypt, check_username_password, allowed_file
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
    # Check if the user is already logged in
    if current_user.is_authenticated:
        username = sqlite.query_userid(current_user.get_id())["username"]
        return redirect(url_for("stream", username=username))
    index_form = IndexForm()
    login_form = index_form.login
    register_form = index_form.register
    if login_form.submit.data and login_form.validate_on_submit():
        # Try to log in the user
        if check_username_password(login_form.username.data, login_form.password.data):
            flash("You have been logged in!", category="success")
            return redirect(url_for("stream", username=login_form.username.data))
        else:
            flash("Invalid username or password!", category="warning")
            # Make a response with status code 401 (Unauthorized)
            return make_response(render_template("index.html", title="Welcome", form=index_form), 401)
    elif register_form.submit.data and register_form.validate_on_submit():
        # Check if user exists
        user = {
            'username': register_form.username.data,
            'password': bcrypt.generate_password_hash(register_form.password.data),
            'first_name': register_form.first_name.data,
            'last_name': register_form.last_name.data,
        }
        if sqlite.check_user_exists(user['username']):
            flash("User already exists!", category="warning")
            return make_response(render_template("index.html", title="Welcome", form=index_form), 400)
        sqlite.insert_user(user)
        flash("User successfully created!", category="success")
        return make_response(render_template("index.html", title="Welcome", form=index_form), 201)
    elif login_form.submit.data or register_form.submit.data:
        flash("Invalid form data!", category="warning")
        return make_response(render_template("index.html", title="Welcome", form=index_form), 400)
    return make_response(render_template("index.html", title="Welcome", form=index_form))

@app.route("/stream/<string:username>", methods=["GET", "POST"])
@login_required
def stream(username: str):
    """Provides the stream page for the application.

    If a form was submitted, it reads the form data and inserts a new post into the database.

    Otherwise, it reads the username from the URL and displays all posts from the user and their friends.
    """
    if not sqlite.check_user_exists(username):
        flash("User does not exist!", category="warning")
        # Redirect user to the index page
        return redirect(url_for("index"))
    post_form = PostForm()
    stream_user_id = sqlite.query_username(username)["id"]
    posts = sqlite.query_posts(stream_user_id)
    if post_form.validate_on_submit():
        filename = ""
        if post_form.image.data:
            if allowed_file(post_form.image.data.filename):
                filename = secure_filename(post_form.image.data.filename)
                path = Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"] / filename 
                post_form.image.data.save(path)
            else:
                flash("Invalid file type!", category="warning")
                return make_response(render_template("stream.html", title="Stream", username=username, form=post_form, posts=posts), 400)
        sqlite.insert_post(current_user.get_id(), post_form.content.data, filename)
        flash("Post successfully created!", category="success")
        # Update the posts
        posts = sqlite.query_posts(stream_user_id)
        return make_response(render_template("stream.html", title="Stream", username=username, form=post_form, posts=posts), 201)
    return make_response(render_template("stream.html", title="Stream", username=username, form=post_form, posts=posts))

@app.route("/comments/<string:username>/<int:post_id>", methods=["GET", "POST"])
@login_required
def comments(username: str, post_id: int):
    """Provides the comments page for the application.
    If a form was submitted, it reads the form data and inserts a new comment into the database.
    Otherwise, it reads the username and post id from the URL and displays all comments for the post.
    """
    if not sqlite.check_user_exists(username) or not sqlite.check_post_exists(post_id):
        flash("User or post does not exist!", category="warning")
        return redirect(url_for("index"))
    post = sqlite.query_post(post_id)
    comments = sqlite.query_comments(post_id)
    comments_form = CommentsForm()
    if comments_form.validate_on_submit():
        sqlite.insert_comment(post_id, comments_form.comment.data, current_user.get_id())
        comments = sqlite.query_comments(post_id)
        return make_response(render_template("comments.html", title="Comments", username=username, form=comments_form, post=post, comments=comments), 201)
    return make_response(render_template("comments.html", title="Comments", username=username, form=comments_form, post=post, comments=comments))

@app.route("/logout")
@login_required
def logout():
    """Logs the user out and redirects them to the index page."""
    logout_user()
    flash("You have been logged out!", category="success")
    return make_response(redirect(url_for("index")))

@app.route("/friends/<string:username>", methods=["GET", "POST"])
@login_required
def friends(username: str):
    """Provides the friends page for the application.
    If a form was submitted, it reads the form data and inserts a new friend into the database.
    Otherwise, it reads the username from the URL and displays all friends of the user.
    """
    if not sqlite.check_user_exists(username):
        flash("User does not exist!", category="warning")
        return redirect(url_for("index"))
    friends_form = FriendsForm()
    friends_user_id = str(sqlite.query_username(username)["id"])
    friends = sqlite.query_friends(friends_user_id)
    if friends_form.validate_on_submit():
        # Check if the current user is the owner of the friendslist being edited
        if current_user.get_id() != str(friends_user_id): 
            flash('You can only add friends to your own friendslist.', category="warning")
            return make_response(render_template("friends.html", title="Friends", username=username, friends=friends, form=friends_form), 401)
        # Find the friend to be added in the database
        friend = sqlite.query_username(friends_form.username.data)
        if friend is None:
            flash("User does not exist!", category="warning")
            return make_response(render_template("friends.html", title="Friends", username=username,friends=friends, form=friends_form), 404)
        elif str(friend["id"]) == current_user.get_id():
            flash("You cannot be friends with yourself!", category="warning")
            return make_response(render_template("friends.html", title="Friends", username=username, friends=friends, form=friends_form), 400)
        # Fetch the friends in the friendlist
        friends = sqlite.query_friends(friends_user_id)
        # Check if the friend is already in the friendlist
        for f in friends:
            if friend["id"] == f["id"]:
                flash("You are already friends with this user!", category="warning")
                return make_response(render_template("friends.html", title="Friends", username=username, friends=friends, form=friends_form), 400)
        # All checks passed, add the friend to the friendlist
        sqlite.insert_friend(current_user.get_id(), friend["id"])
        flash("Friend successfully added!", category="success") 
        # Refresh the friends list
        friends = sqlite.query_friends(friends_user_id)
    return make_response(render_template("friends.html", title="Friends", username=username, friends=friends, form=friends_form)
    )

@app.route("/profile/<string:username>", methods=["GET", "POST"])
@login_required
def profile(username: str):
    """Provides the profile page for the application.
    If a form was submitted, it reads the form data and updates the user's profile in the database.
    Otherwise, it reads the username from the URL and displays the user's profile.
    """
    if not sqlite.check_user_exists(username):
        flash("User does not exist!", category="warning")
        return redirect(url_for("index"))
    profile_form = ProfileForm()
    user = sqlite.query_userprofile(username)
    if not user["id"] or not current_user.get_id():
        flash("User does not exist!", category="warning")
        return make_response(render_template("profile.html", title="Profile", username=username, user=user, form=profile_form), 404)
    if profile_form.validate_on_submit():
        # Check if the current user is the same as the user whose profile is being updated
        if current_user.get_id() != str(user["id"]):
            flash("You cannot update another user's profile!", category="warning")
            return make_response(render_template("profile.html", title="Profile", username=username, user=user, form=profile_form), 401)
        data = {
            "education": profile_form.education.data if profile_form.education.data else None,
            "employment": profile_form.employment.data if profile_form.employment.data else None,
            "music": profile_form.music.data if profile_form.music.data else None,
            "movie": profile_form.movie.data if profile_form.movie.data else None,
            "nationality": profile_form.nationality.data if profile_form.nationality.data else None,
            "birthday": profile_form.birthday.data if profile_form.birthday.data else None,
        }
        sqlite.update_profile(current_user.get_id(), data) 
        # Update the profile
        user = sqlite.query_userprofile(username)
    return make_response(render_template("profile.html", title="Profile", username=username, user=user, form=profile_form))

@app.route("/uploads/<string:filename>")
@login_required
def uploads(filename):
    """Provides an endpoint for serving uploaded files."""
    # Check if file exists
    if not Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"] / filename:
        flash("File does not exist!", category="warning")
        return make_response(render_template("index.html", title="Welcome", form=IndexForm()), 404)
    return send_from_directory(Path(app.instance_path) / app.config["UPLOADS_FOLDER_PATH"], filename)
