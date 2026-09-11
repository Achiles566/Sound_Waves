"""
Database models for SoundWave.

Three tables, as requested:
  - users    -> login credentials and identity
  - profiles -> the public-facing profile info (bio, avatar), one per user
  - songs    -> uploaded tracks, each belonging to one user

We use Flask-SQLAlchemy, which lets us describe tables as Python classes
instead of writing raw SQL for every query.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """A registered account. UserMixin adds the methods Flask-Login needs
    (is_authenticated, get_id, etc.) so we don't have to write them by hand.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # We NEVER store the raw password - only a secure hash of it.
    # See app.py's signup route for how this gets set.
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One-to-one with Profile, one-to-many with Song.
    # cascade="all, delete-orphan" means: if a user is deleted, their
    # profile and songs are cleaned up automatically instead of left orphaned.
    profile = db.relationship(
        "Profile", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    songs = db.relationship(
        "Song", backref="uploader", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Profile(db.Model):
    """Public-facing profile info, kept separate from login credentials."""

    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    bio = db.Column(db.Text, default="")

    # Stored as a path relative to /static, e.g. "uploads/avatars/xyz.png".
    # Empty string means "use the default avatar".
    avatar_path = db.Column(db.String(255), default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Profile of user_id={self.user_id}>"


class Song(db.Model):
    """An uploaded track."""

    __tablename__ = "songs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(150), nullable=False)
    artist = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")

    # Paths relative to /static, same idea as avatar_path above.
    cover_path = db.Column(db.String(255), default="")
    audio_path = db.Column(db.String(255), nullable=False)

    plays = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Song {self.title} by {self.artist}>"
