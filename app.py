"""
SoundWave - main Flask application.

This one file wires everything together: app setup, login handling, and
every route (page) the site has. It's organized top-to-bottom into clearly
labeled sections so it's easy to follow even if you're new to Flask.
"""

import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Profile, Song


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to view that page."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(user_id):
    # Flask-Login calls this on every request to figure out who's logged in,
    # based on the user id stored in the session cookie.
    return db.session.get(User, int(user_id))


# Make sure the folders we save uploads into actually exist.
for folder in (Config.AUDIO_FOLDER, Config.COVER_FOLDER, Config.AVATAR_FOLDER):
    os.makedirs(folder, exist_ok=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def allowed_file(filename, allowed_extensions):
    """True if filename ends in one of the allowed extensions."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_upload(file_storage, folder, allowed_extensions):
    """
    Validate and save an uploaded file.

    Returns the path to store in the database (relative to /static), or
    None if there was no file to save. Raises ValueError if the file type
    isn't allowed - callers should catch this and show the user an error.
    """
    if not file_storage or file_storage.filename == "":
        return None

    filename = secure_filename(file_storage.filename)

    if not allowed_file(filename, allowed_extensions):
        raise ValueError(
            f"'.{filename.rsplit('.', 1)[-1]}' files aren't allowed here."
        )

    # Prefix with a random id so two users' "cover.jpg" never collide.
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file_storage.save(os.path.join(folder, unique_name))

    # Figure out the folder name relative to static/uploads for the URL/DB path.
    folder_name = os.path.basename(folder.rstrip("/"))
    return f"uploads/{folder_name}/{unique_name}"


# ---------------------------------------------------------------------------
# Pages: home + search
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    songs = Song.query.order_by(Song.created_at.desc()).limit(30).all()
    return render_template("index.html", songs=songs, query=None)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    if query:
        like_pattern = f"%{query}%"
        songs = (
            Song.query.filter(
                db.or_(
                    Song.title.ilike(like_pattern),
                    Song.artist.ilike(like_pattern),
                )
            )
            .order_by(Song.created_at.desc())
            .all()
        )
    else:
        songs = []

    return render_template("index.html", songs=songs, query=query)


# ---------------------------------------------------------------------------
# Auth: signup, login, logout
# ---------------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- Validation ---
        error = None
        if len(username) < 3 or len(username) > 50:
            error = "Username must be between 3 and 50 characters."
        elif not username.replace("_", "").isalnum():
            error = "Username can only contain letters, numbers, and underscores."
        elif "@" not in email or "." not in email:
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords don't match."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "error")
            return render_template("signup.html", username=username, email=email)

        # --- Create the account ---
        # generate_password_hash salts and hashes the password with a strong
        # algorithm (scrypt by default). The raw password is never stored.
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(new_user)
        db.session.flush()  # so new_user.id is available for the Profile below

        db.session.add(Profile(user_id=new_user.id))
        db.session.commit()

        login_user(new_user)
        flash(f"Welcome to SoundWave, {username}!", "success")
        return redirect(url_for("index"))

    return render_template("signup.html", username="", email="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # check_password_hash re-hashes the submitted password with the same
        # salt and compares - it never needs to know the original password.
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))

        flash("Incorrect email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        artist = request.form.get("artist", "").strip()
        description = request.form.get("description", "").strip()
        audio_file = request.files.get("audio_file")
        cover_file = request.files.get("cover_file")

        if not title or not artist:
            flash("Title and artist are required.", "error")
            return render_template("upload.html")

        if not audio_file or audio_file.filename == "":
            flash("Please choose an audio file.", "error")
            return render_template("upload.html")

        try:
            audio_path = save_upload(
                audio_file, Config.AUDIO_FOLDER, Config.ALLOWED_AUDIO_EXTENSIONS
            )
            cover_path = save_upload(
                cover_file, Config.COVER_FOLDER, Config.ALLOWED_IMAGE_EXTENSIONS
            )
        except ValueError as e:
            flash(str(e), "error")
            return render_template("upload.html")

        song = Song(
            user_id=current_user.id,
            title=title,
            artist=artist,
            description=description,
            audio_path=audio_path,
            cover_path=cover_path or "",
        )
        db.session.add(song)
        db.session.commit()

        flash("Track uploaded!", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("upload.html")


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    songs = (
        Song.query.filter_by(user_id=user.id)
        .order_by(Song.created_at.desc())
        .all()
    )
    return render_template(
        "profile.html",
        profile_user=user,
        songs=songs,
        is_own_profile=current_user.is_authenticated and current_user.id == user.id,
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    profile_row = current_user.profile

    if request.method == "POST":
        bio = request.form.get("bio", "").strip()
        avatar_file = request.files.get("avatar_file")

        if len(bio) > 500:
            flash("Bio must be 500 characters or fewer.", "error")
            return render_template("edit_profile.html", profile_row=profile_row)

        try:
            avatar_path = save_upload(
                avatar_file, Config.AVATAR_FOLDER, Config.ALLOWED_IMAGE_EXTENSIONS
            )
        except ValueError as e:
            flash(str(e), "error")
            return render_template("edit_profile.html", profile_row=profile_row)

        profile_row.bio = bio
        if avatar_path:
            profile_row.avatar_path = avatar_path

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile", username=current_user.username))

    return render_template("edit_profile.html", profile_row=profile_row)


# ---------------------------------------------------------------------------
# Small JSON API: play count
# ---------------------------------------------------------------------------

@app.route("/api/songs/<int:song_id>/play", methods=["POST"])
def register_play(song_id):
    song = db.session.get(Song, song_id)
    if not song:
        abort(404)
    song.plays = (song.plays or 0) + 1
    db.session.commit()
    return jsonify({"plays": song.plays})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(413)
def file_too_large(e):
    flash("That file is too large. Max upload size is 30MB.", "error")
    return redirect(request.referrer or url_for("index"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # creates database.db and its tables if they don't exist yet
    app.run(debug=True)
