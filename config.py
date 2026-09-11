"""
Configuration for the SoundWave app.

We keep all settings in one place, and pull secrets (like SECRET_KEY) from
environment variables instead of hard-coding them in the source code.
python-dotenv loads variables from a local .env file (which is NOT committed
to version control - see .env.example for the template).
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY signs session cookies. In production this MUST come from
    # an environment variable. The fallback here only exists so the app
    # still runs the first time you try it, during local development.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")

    # SQLite database file, stored at the project root.
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Where uploaded files get saved on disk.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    AUDIO_FOLDER = os.path.join(UPLOAD_FOLDER, "audio")
    COVER_FOLDER = os.path.join(UPLOAD_FOLDER, "covers")
    AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, "avatars")

    # Reject any upload request larger than this (in bytes). 30 MB.
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024

    # Only these file extensions are accepted. Anything else is rejected,
    # even if the user renames a file to make it look like an mp3.
    ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a"}
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
