from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING
from flask_login import current_user
import pytest
from io import BytesIO

from app import app, sqlite

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient

@pytest.fixture(scope="session")
def test_app() -> Iterator[Flask]:
    app.config.update(
        {
            "SQLITE3_DATABASE": "file::memory:?cache=shared",
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test",
        }
    )
    yield app


@pytest.fixture()
def client(test_app: Flask) -> FlaskClient:
    return test_app.test_client()


@pytest.fixture()
def logged_in_client(client: FlaskClient, userid:int = 0) -> FlaskClient:
    with client:
        client.post(
            "/",
            data = {
                "login-username": users[userid]["username"],
                "login-password": users[userid]["password"],
                "login-submit": "Sign In",
            }
        )
        assert current_user.is_authenticated is True
    yield client

@pytest.fixture()
def logged_in_client2(client: FlaskClient, userid:int = 1) -> FlaskClient:
    with client:
        client.post(
            "/",
            data = {
                "login-username": users[userid]["username"],
                "login-password": users[userid]["password"],
                "login-submit": "Sign In",
            }
        )
        assert current_user.is_authenticated is True
    yield client

# Users to test registration and login
users = [
    {
        "description": "New user with valid data",
        "expected_status_code_registration": 201,
        "expected_status_code_login": 302,
        "first_name": "test",
        "last_name": "test",
        "username": "test",
        "password": "test1234",
    },
    {
        "description": "New user with valid data",
        "expected_status_code_registration": 201,
        "expected_status_code_login": 302,
        "first_name": "test1",
        "last_name": "test1",
        "username": "test1", 
        "password": "1test1234",
    },
    {
        "description": "New user with valid data",
        "expected_status_code_registration": 201,
        "expected_status_code_login": 302,
        "first_name": "test2",
        "last_name": "test2",
        "username": "test2",
        "password": "2test1234",
    },
    {
        "description": "New user with duplicate username",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 401,
        "first_name": "test",
        "last_name": "test",
        "username": "test",
        "password": "wrong_password",
    },
    {
        "description": "New user with too short password",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 400,
        "first_name": "test",
        "last_name": "test",
        "username": "too_short_password",
        "password": "test",
    },
    {
        "description": "New user with too long password",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 400,
        "first_name": "test",
        "last_name": "test",
        "username": "too_long_password",
        "password": "test" * 100,
    },
    {
        "description": "New user with too long first name",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 401,
        "first_name": "test" * 100,
        "last_name": "test",
        "username": "too_long_first_name",
        "password": "test1234",
    },
    {
        "description": "New user with too long last name",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 401,
        "first_name": "test",
        "last_name": "test" * 100,
        "username": "too_long_last_name",
        "password": "test1234",
    },
    {
        "description": "New user with missing first name",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 401,
        "first_name": "",
        "last_name": "test",
        "username": "missing_first_name",
        "password": "test1234",
    },
    {
        "description": "New user with missing last name",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 401,
        "first_name": "test",
        "last_name": "",
        "username": "missing_last_name",
        "password": "test1234",
    },
    {
        "description": "New user with missing username",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 400,
        "first_name": "test",
        "last_name": "test",
        "username": "",
        "password": "test1234",
    },
    {
        "description": "New user with missing password",
        "expected_status_code_registration": 400,
        "expected_status_code_login": 400,
        "first_name": "test",
        "last_name": "test",
        "username": "missing_password",
        "password": "",
    },
]


@pytest.mark.parametrize("user", users)
def test_register(client: FlaskClient, user: dict):
    with app.app_context():
        response = client.post(
            "/",
            data={
                "register-first_name": user["first_name"],
                "register-last_name": user["last_name"],
                "register-username": user["username"],
                "register-password": user["password"],
                "register-confirm_password": user["password"],
                "register-submit": "Sign Up",
            }
        )
        assert response.status_code == user["expected_status_code_registration"], f"Registration test failed for user: {user['description']}."
        # Check that the user is in the database for the expected successful registrations
        if user["expected_status_code_registration"] == 201 or user["description"] == "New user with duplicate username":    
            assert sqlite.check_user_exists(user["username"]) is True, f"Registration test failed for user: {user['description']}."
        # Check that the user is not in the database for the expected failures
        else:
            assert sqlite.check_user_exists(user["username"]) is False, f"Registration test failed for user: {user['description']}."

@pytest.mark.parametrize("user", users)
def test_login(client: FlaskClient, user: dict):
    with client:
        response = client.post(
            "/",
            data={
                "login-username": user["username"],
                "login-password": user["password"],
                "login-submit": "Sign In",
            }
        )
        assert response.status_code == user['expected_status_code_login'], f"Login test failed for user: {user['description']}."
        # Assert that the user is authenticated for the expected successful logins 
        if user['expected_status_code_login'] == 302:
            assert current_user.is_authenticated, f"Login test failed for user: {user['description']}."
        # Assert that the user is not authenticated for the expected failures
        else:
            assert not current_user.is_authenticated, f"Login test failed for user: {user['description']}."

######################## TEST ROUTES GET REQUEST WHILE LOGGED IN ########################
def test_get_index_logged_in(logged_in_client: FlaskClient):
    with logged_in_client:
        response = logged_in_client.get("/")
        assert response.status_code == 302
        assert response.location == "/stream/test"

def test_get_index2_logged_in(logged_in_client: FlaskClient):
    with logged_in_client:
        response = logged_in_client.get("/index")
        assert response.status_code == 302
        # Check that the user is redirected to the stream page
        assert response.location == "/stream/test"

def test_get_stream_logged_in(logged_in_client: FlaskClient):
    with logged_in_client:
        response = logged_in_client.get("/stream/test")
        assert response.status_code == 200

def test_get_friends_logged_in(logged_in_client: FlaskClient):
    with logged_in_client:
        response = logged_in_client.get("/friends/test")
        assert response.status_code == 200

def test_get_profile_logged_in(logged_in_client: FlaskClient):
    with logged_in_client:
        response = logged_in_client.get("/profile/test")
        assert response.status_code == 200

def test_get_logout_logged_in(client: FlaskClient):
    response = client.get("/logout")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"


# Test various post requests to the /stream
def test_post_stream_valid(logged_in_client: FlaskClient):
    with app.app_context():
        with open('test_upload.png', 'rb') as f:
            image_data = f.read()
        data = {
            "content": "test",
            "image": (BytesIO(image_data), 'test_upload.png'),
            "submit": "Post",
        }
        response = logged_in_client.post("/stream/test", data=data, content_type='multipart/form-data')
        assert response.status_code == 201
        # Assert that the image was uploaded 
        response = logged_in_client.get(f"/uploads/{data['image'][1]}")
        assert response.status_code == 200
        # Assert that the post is in the database
        assert sqlite.check_post_exists(1) is True

def test_post_stream_invalid_filename(logged_in_client: FlaskClient):
    with app.app_context():
        with open('virus.exe', 'rb') as f:
            image_data = f.read()
        data = {
            "content": "test",
            "image": (BytesIO(image_data), 'virus.exe'),
            "submit": "Post",
        }
        response = logged_in_client.post("/stream/test", data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        # Assert that the image was not uploaded
        response = logged_in_client.get(f"/uploads/{data['image'][1]}")
        assert response.status_code == 404
        # Assert that the post is not in the database
        assert sqlite.check_post_exists(2) is False

def test_post_stream_too_long_content(logged_in_client: FlaskClient):
    with app.app_context():
        with open('test_upload.png', 'rb') as f:
            image_data = f.read()
        data = {
            "content": "t" * 501,
            "image": (BytesIO(image_data), 'test_upload2.png'),
            "submit": "Post",
        }
        response = logged_in_client.post("/stream/test", data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        # Assert that the image was uploaded 
        response = logged_in_client.get(f"/uploads/{data['image'][1]}")
        assert response.status_code == 404
        # Assert that the post is in the database
        assert sqlite.check_post_exists(2) is False

def test_post_stream_no_file(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "content": "No file",
            "submit": "Post",
        }
        response = logged_in_client.post("/stream/test", data=data, content_type='multipart/form-data')
        assert response.status_code == 201
        # Assert that the post is in the database
        assert sqlite.check_post_exists(2) is True

def test_post_stream_no_content(logged_in_client: FlaskClient):
    with app.app_context():
        with open('test_upload2.png', 'rb') as f:
            image_data = f.read()
        data = {
            "image": (BytesIO(image_data), 'test_upload2.png'),
            "submit": "Post",
        }
        response = logged_in_client.post("/stream/test", data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        # Assert that the image was not uploaded 
        response = logged_in_client.get(f"/uploads/{data['image'][1]}")
        assert response.status_code == 404
        # Assert that the post is not in the database
        assert sqlite.check_post_exists(3) is False

###################### COMMENTS ######################
def test_get_comments_logged_in(logged_in_client: FlaskClient):
    with app.app_context():
        response = logged_in_client.get("/comments/test/1")
        assert response.status_code == 200

def test_get_comments_logged_in_invalid_post_id(logged_in_client: FlaskClient):
    with app.app_context():
        response = logged_in_client.get("/comments/test/100")
        assert response.status_code == 302

def test_get_comments_logged_in_invalid_username(logged_in_client: FlaskClient):
    with app.app_context():
        response = logged_in_client.get("/comments/invalid/1")
        assert response.status_code == 302

def test_post_comments_valid(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "comment": "test",
            "submit": "Comment",
        }
        response = logged_in_client.post("/comments/test/1", data=data)
        assert response.status_code == 201
        # Assert that the comment is in the database
        assert sqlite.check_comment_exists(1) is True

def test_post_comments_too_long_content(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "comment": "t" * 501,
            "submit": "Comment",
        }
        response = logged_in_client.post("/comments/test/1", data=data)
        assert response.status_code == 200
        # Assert that the comment is not in the database
        assert sqlite.check_comment_exists(2) is False

def test_post_comments_no_content(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "submit": "Comment",
        }
        response = logged_in_client.post("/comments/test/1", data=data)
        assert response.status_code == 200
        # Assert that the comment is not in the database
        assert sqlite.check_comment_exists(2) is False

def test_post_comments_no_submit(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "comment": "test",
        }
        response = logged_in_client.post("/comments/test/1", data=data)
        assert response.status_code == 200
        # Assert that the comment is not in the database
        assert sqlite.check_comment_exists(2) is False

######### PROFILE UPDATES #########
def test_post_profile_updates(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "education": "test",
            "employment": "test",
            "submit": "Update Profile",
        }
        response = logged_in_client.post("/profile/test", data=data)
        assert response.status_code == 201
        profile_data = sqlite.query_userprofile("test") 
        assert profile_data["education"] == "test"
        assert profile_data["employment"] == "test"

def test_post_profile_updates_other_user(logged_in_client2: FlaskClient):
    with app.app_context():
        data = {
            "education": "test2",
            "employment": "test2",
            "submit": "Update Profile",
        }
        response = logged_in_client2.post("/profile/test", data=data)
        assert response.status_code == 401
        profile_data = sqlite.query_userprofile("test")
        assert profile_data["education"] == "test"
        assert profile_data["employment"] == "test"

def test_post_profile_updates_user_not_found(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "education": "test",
            "employment": "test",
            "submit": "Update Profile",
        }
        response = logged_in_client.post("/profile/invalid", data=data)
        assert response.status_code == 302

###################### FRIENDS ######################
def test_post_friends_valid(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "username": "test1",
            "submit": "Add Friend",
        }
        response = logged_in_client.post("/friends/test", data=data)
        assert response.status_code == 201
        # Assert that the friend is in the database
        assert sqlite.check_friend_connection(1, 2) is True

def duplicate_friend_request(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "username": "test1",
            "submit": "Add Friend",
        }
        response = logged_in_client.post("/friends/test", data=data)
        assert response.status_code == 400

def friend_request_self(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "username": "test",
            "submit": "Add Friend",
        }
        response = logged_in_client.post("/friends/test", data=data)
        assert response.status_code == 400

def test_post_friends_invalid_username(logged_in_client: FlaskClient):
    with app.app_context():
        data = {
            "username": "invalid",
            "submit": "Add Friend",
        }
        response = logged_in_client.post("/friends/test", data=data)
        assert response.status_code == 404
        # Assert that the friend is not in the database
        assert sqlite.check_friend_connection(1, 3) is False


############## ALL ROUTES WHILE NOT LOGGED IN ##############
def test_get_index(client: FlaskClient):
    response = client.get("/")
    assert response.status_code == 200

def test_get_index2(client: FlaskClient):
    response = client.get("/index")
    assert response.status_code == 200

def test_get_stream(client: FlaskClient):
    response = client.get("/stream/random")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"

def test_get_comments(client: FlaskClient):
    response = client.get("/comments/test/1")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"

def test_get_friends(client: FlaskClient):
    response = client.get("/friends/test")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"

def test_get_profile(client: FlaskClient):
    response = client.get("/profile/test")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"

def test_get_upload(client: FlaskClient):
    response = client.get("/uploads/test")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"

def test_get_logout(client: FlaskClient):
    response = client.get("/logout")
    assert response.status_code == 302
    # Assert that the user is redirected to the login page
    assert response.location == "/" or response.location == "/index"