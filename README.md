# SoundWave

A music-sharing website: create an account, upload tracks, browse and search
other people's uploads, and play them with a full bottom music player.

Built with:
- **Backend**: Python + Flask
- **Database**: SQLite (via Flask-SQLAlchemy)
- **Auth**: Flask-Login + Werkzeug's password hashing
- **Frontend**: plain HTML (Jinja2 templates), CSS, and vanilla JavaScript
  — no React, Vue, or any frontend framework

## Project structure

```
SoundWave/
├── app.py              # the Flask app: every route lives here
├── models.py            # database tables: User, Profile, Song
├── config.py             # settings, reads secrets from environment variables
├── requirements.txt
├── .env.example          # copy to .env and fill in your own secret key
├── database.db           # created automatically the first time you run the app
├── templates/            # HTML pages (Jinja2)
│   ├── base.html          # navbar, search bar, flash messages, player bar
│   ├── index.html         # home page + search results
│   ├── signup.html
│   ├── login.html
│   ├── upload.html
│   ├── profile.html
│   ├── edit_profile.html
│   └── 404.html
└── static/
    ├── css/style.css     # all the styling
    ├── js/
    │   ├── main.js         # mobile nav + flash message behavior
    │   └── player.js       # the bottom music player
    ├── images/default-cover.svg
    └── uploads/            # uploaded audio, covers, and avatars land here
        ├── audio/
        ├── covers/
        └── avatars/
```

## 1. Set up a virtual environment

A virtual environment keeps this project's Python packages separate from
everything else on your machine.

```bash
cd SoundWave
python3 -m venv venv

# Activate it:
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

You'll know it worked if you see `(venv)` at the start of your terminal
prompt.

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure your secret key

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder with a real random value. You
can generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the result in as `SECRET_KEY=...`. This key signs login session
cookies — never share it or commit it to a public repo (`.env` is already
excluded via `.gitignore`).

## 4. Run the app

```bash
python app.py
```

The first time you run this, it creates `database.db` automatically with
empty `users`, `profiles`, and `songs` tables — no manual database setup
needed.

Open **http://127.0.0.1:5000** in your browser. Sign up for an account, then
upload a track from the "Upload" button in the navbar.

## How the pieces fit together

- **`config.py`** holds settings like the database location and which file
  types are allowed. It reads `SECRET_KEY` from your `.env` file instead of
  hard-coding it, so secrets never end up in the source code.
- **`models.py`** defines three database tables as Python classes:
  `User` (login credentials), `Profile` (bio + avatar), and `Song`
  (uploaded tracks). SQLAlchemy turns these into real SQLite tables.
- **`app.py`** is where every page ("route") is defined — signup, login,
  upload, profile, search, and so on. Routes marked `@login_required` are
  only reachable if you're logged in; anyone else gets redirected to the
  login page.
- **Passwords** are never stored as plain text. `generate_password_hash()`
  turns a password into a one-way hash before saving it, and
  `check_password_hash()` verifies a login attempt without ever needing to
  know the original password.
- **File uploads** are checked against an allow-list of extensions
  (`.mp3`, `.wav`, etc. for audio; `.png`, `.jpg`, etc. for images) before
  being saved with a randomized filename, so users can't upload arbitrary
  file types or overwrite each other's files.
- **`static/js/player.js`** builds a "queue" from whatever `.song-card`
  elements are on the current page (home feed, search results, or a
  profile), so Next/Previous just moves through that list. Clicking any
  card loads its track into the single `<audio>` element in the bottom bar.

## Things worth knowing as you build on this

- **Production secret key**: the fallback key in `config.py` is only for
  first-run convenience. Always set a real `SECRET_KEY` via `.env` (or your
  host's environment variable settings) before deploying anywhere public.
- **SQLite in production**: SQLite is great for development and small
  projects, but for a real public launch with many simultaneous users,
  consider PostgreSQL — Flask-SQLAlchemy makes that swap mostly a one-line
  change to `SQLALCHEMY_DATABASE_URI`.
- **Debug mode**: `app.run(debug=True)` is convenient locally (auto-reload,
  detailed error pages) but must never be used in production — it can leak
  sensitive information. Use a proper WSGI server like Gunicorn instead.
- **Play counts**: the `songs.plays` column is already wired up — every
  time a track starts playing, `player.js` calls a small JSON API endpoint
  that increments it.
