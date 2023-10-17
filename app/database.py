"""Provides a SQLite3 database extension for Flask.

This extension provides a simple interface to the SQLite3 database.

Example:
    from flask import Flask
    from app.database import SQLite3

    app = Flask(__name__)
    db = SQLite3(app)
"""

from __future__ import annotations

import sqlite3
from os import PathLike
from pathlib import Path
from typing import Any, Optional, cast

from flask import Flask, current_app, g


class SQLite3:
    """Provides a SQLite3 database extension for Flask.

    This class provides a simple interface to the SQLite3 database.
    It also initializes the database if it does not exist yet.

    Example:
        from flask import Flask
        from app.database import SQLite3

        app = Flask(__name__)
        db = SQLite3(app)

        # Use the database
        # db.query("SELECT * FROM Users;")
        # db.query("SELECT * FROM Users WHERE id = 1;", one=True)
        # db.query("INSERT INTO Users (name, email) VALUES ('John', 'test@test.net');")
    """

    def __init__(
        self,
        app: Optional[Flask] = None,
        *,
        path: Optional[PathLike | str] = None,
        schema: Optional[PathLike | str] = None,
    ) -> None:
        """Initializes the extension.

        params:
            app: The Flask application to initialize the extension with.
            path (optional): The path to the database file. Is relative to the instance folder.
            schema (optional): The path to the schema file. Is relative to the application root folder.

        """
        if app is not None:
            self.init_app(app, path=path)

    def init_app(
        self,
        app: Flask,
        *,
        path: Optional[PathLike | str] = None,
        schema: Optional[PathLike | str] = None,
    ) -> None:
        """Initializes the extension.

        params:
            app: The Flask application to initialize the extension with.
            path (optional): The path to the database file. Is relative to the instance folder.
            schema (optional): The path to the schema file. Is relative to the application root folder.

        """
        if not hasattr(app, "extensions"):
            app.extensions = {}

        if "sqlite3" not in app.extensions:
            app.extensions["sqlite3"] = self
        else:
            raise RuntimeError("Flask SQLite3 extension already initialized")

        if path == ":memory:" or app.config.get("SQLITE3_DATABASE_PATH") == ":memory:":
            raise ValueError("Cannot use in-memory database with Flask SQLite3 extension")

        if path:
            self._path = Path(app.instance_path) / path
        elif "SQLITE3_DATABASE_PATH" in app.config:
            self._path = Path(app.instance_path) / app.config["SQLITE3_DATABASE_PATH"]
        else:
            self._path = Path(app.instance_path) / "sqlite3.db"

        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)

        if schema:
            with app.app_context():
                self._init_database(schema)
        app.teardown_appcontext(self._close_connection)

    @property
    def connection(self) -> sqlite3.Connection:
        """Returns the connection to the SQLite3 database."""
        conn = getattr(g, "flask_sqlite3_connection", None)
        if conn is None:
            conn = g.flask_sqlite3_connection = sqlite3.connect(self._path)
            conn.row_factory = sqlite3.Row
        return conn

    def query_friends(self, user_id: str) -> list[sqlite3.Row] | None:
        cursor = self.connection.execute(
            """
            SELECT U.id, U.username
            FROM Users U
            JOIN Friends F ON U.id = F.f_id
            WHERE F.u_id = ?
            """, (user_id,)
        )
        friends = cursor.fetchall()
        return friends

    def query_userid(self, userid) -> dict | None:
        """Fetch userid from the database."""
        cursor = self.connection.execute(
            "SELECT id, username, first_name, last_name FROM Users WHERE id = ?", (userid,)
            )
        user = cursor.fetchone()
        return user
    
    def query_userprofile(self, username: str) -> sqlite3.Row | None:
        """Fetch userprofile data from the database."""
        cursor = self.connection.execute(
            "SELECT id, first_name, last_name, education, employment, music, movie, nationality, birthday FROM Users WHERE username = ?", (username,)
            )
        user = cursor.fetchone()
        return user
    
    def query_username(self, username) -> sqlite3.Row | None:
        """Fetch user from the database."""
        cursor = self.connection.execute(
            "SELECT id, username, password, first_name, last_name FROM Users WHERE username = ?", (username,)
            )
        user = cursor.fetchone()
        return user

    def query_posts(self, userid: str) -> list[sqlite3.Row] | None:
        """Fetch posts from the database."""
        cursor = self.connection.execute(
         """
         SELECT p.*, u.id, u.username,
         (SELECT COUNT(*) FROM Comments WHERE p_id = p.id) AS cc
         FROM Posts AS p JOIN Users AS u ON u.id = p.u_id
         WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id = ?) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id = ?) OR p.u_id = ? 
         ORDER BY p.creation_time DESC;
        """, (userid, userid, userid)
        )
        posts = cursor.fetchall()
        return posts
    
    def query_post(self, post_id: str) -> sqlite3.Row | None:
        """Fetch post from the database."""
        cursor = self.connection.execute(
        """
        SELECT *
        FROM Posts AS p JOIN Users AS u ON p.u_id = u.id
        WHERE p.id = ?;
        """, (post_id,)
            )
        post = cursor.fetchone()
        return post
    
    def query_comments(self, post_id: str) -> list[sqlite3.Row] | None:
        """Fetch comments from the database."""
        cursor = self.connection.execute(
        """
        SELECT DISTINCT *
        FROM Comments AS c JOIN Users AS u ON c.u_id = u.id
        WHERE c.p_id = ?
        ORDER BY c.creation_time DESC;
        """, (post_id,)
        )
        comments = cursor.fetchall()
        return comments

    def check_user_exists(self, username) -> bool:
        cursor = self.connection.execute(
            "SELECT id FROM Users WHERE username = ?", (username,)
            )
        user = cursor.fetchone()
        if user:
            return True
        return False
    
    def insert_user(self, user:dict) -> None:
        """Insert user into the database."""
        cursor = self.connection.execute(
            "INSERT INTO Users (username, password, first_name, last_name) VALUES (?, ?, ?, ?)",
             (user.get('username'), user.get('password'), user.get('first_name'), user.get('last_name'))
            )
        self.connection.commit()

    def insert_post(self, user_id, content, image ) -> None:
        """Insert post into the database."""
        self.connection.execute(
            "INSERT INTO Posts (u_id, content, image, creation_time) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (user_id, content, image)
            )
        self.connection.commit()

    def insert_friend(self, user_id, friend_id) -> None:
        cursor = self.connection.execute(
        """
        INSERT INTO Friends (u_id, f_id)
        VALUES (?, ?);
        """, (user_id, friend_id)
        )
        # Check how many rows were inserted
        print(cursor.rowcount)
        self.connection.commit()

    def insert_comment(self, post_id, comment, user_id) -> None:
        """Insert comment into the database."""
        print(post_id, comment, user_id)
        self.connection.execute(
            """
            INSERT INTO Comments (p_id, u_id, comment, creation_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP);
            """, (post_id, user_id, comment)
        )
        self.connection.commit()

    def update_profile(self, user_id, data: dict) -> None:
        self.connection.execute(
            """
            UPDATE Users
            SET
            education = CASE WHEN ? IS NOT NULL THEN ? ELSE education END,
            employment = CASE WHEN ? IS NOT NULL THEN ? ELSE employment END,
            music = CASE WHEN ? IS NOT NULL THEN ? ELSE music END,
            movie = CASE WHEN ? IS NOT NULL THEN ? ELSE movie END,
            nationality = CASE WHEN ? IS NOT NULL THEN ? ELSE movie END,
            birthday = CASE WHEN ? IS NOT NULL THEN ? ELSE birthday END
            WHERE id = ?;
            """, (
                data.get("education"),
                data.get("education"),
                data.get("employment"),
                data.get("employment"),
                data.get("music"),
                data.get("music"),
                data.get("movie"),
                data.get("movie"),
                data.get("nationality"),
                data.get("nationality"),
                data.get("birthday"),
                data.get("birthday"),
                user_id
                )
        )
        self.connection.commit()

    def _init_database(self, schema: PathLike | str) -> None:
        """Initializes the database with the supplied schema if it does not exist yet."""
        with current_app.open_resource(str(schema), mode="r") as file:
            self.connection.executescript(file.read())
            self.connection.commit()

    def _close_connection(self, exception: Optional[BaseException] = None) -> None:
        """Closes the connection to the database."""
        conn = cast(sqlite3.Connection, getattr(g, "flask_sqlite3_connection", None))
        if conn is not None:
            conn.close()
