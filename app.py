from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_session import Session
from cs50 import SQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime


# ----------------------------
# BASIC CONFIGURATION
# ----------------------------

app = Flask(__name__)

# Secret key for sessions
app.config["SECRET_KEY"] = "dev-secret-key-change-later"

# CS50 Finance style session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connecting to the SQLite database
db = SQL("sqlite:///eventmatch.db")


def get_db_connection():
    conn = sqlite3.connect("eventmatch.db")
    conn.row_factory = sqlite3.Row
    return conn

def parse_hhmm(value):
    """Convierte 'HH:MM' en datetime.time o None si viene vacío/raro."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None
# ----------------------------
# DECORATOR login_required
# ----------------------------

def login_required(f):
    """Evitar acceder a rutas sin iniciar sesión."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.after_request
def after_request(response):
    """Evitar cacheo (estilo CS50)."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = 0
    return response


# ----------------------------
# MAIN ROUTE
# ----------------------------

@app.route("/")
def index():
    return render_template("index.html")

# ----------------------------
# LIST OF EVENTS
# ----------------------------

@app.route("/events")
def events_list():
    events = db.execute(
        "SELECT * FROM events ORDER BY start_date IS NULL, start_date"
    )

    current_event_id = session.get("current_event_id")
    current_event_name = session.get("current_event_name")

    return render_template(
        "events.html",
        events=events,
        current_event_id=current_event_id,
        current_event_name=current_event_name,
    )


# ----------------------------
# EVENT DETAILS
# ----------------------------

@app.route("/events/<int:event_id>")
def event_detail(event_id):
    # 1) Event information
    rows = db.execute("SELECT * FROM events WHERE id = ?", event_id)
    if len(rows) != 1:
        flash("Event not found.")
        return redirect("/events")

    event = rows[0]

    # 2) Event talks
    talks = db.execute(
        """
        SELECT * FROM talks
        WHERE event_id = ?
        ORDER BY start_time
        """,
        event_id
    )

    # 3) Event exhibitors
    exhibitors = db.execute(
        """
        SELECT * FROM exhibitors
        WHERE event_id = ?
        ORDER BY name
        """,
        event_id
    )

    # 4) If the user is logged in, see what they already have in their agenda
    saved_talk_ids = set()
    saved_exhibitor_ids = set()

    user_id = session.get("user_id")
    if user_id:
        rows_talks = db.execute(
            "SELECT talk_id FROM user_talks WHERE user_id = ?",
            user_id
        )
        saved_talk_ids = {row["talk_id"] for row in rows_talks}

        rows_exh = db.execute(
            "SELECT exhibitor_id FROM user_exhibitors WHERE user_id = ?",
            user_id
        )
        saved_exhibitor_ids = {row["exhibitor_id"] for row in rows_exh}

    return render_template(
        "event_detail.html",
        event=event,
        talks=talks,
        exhibitors=exhibitors,
        saved_talk_ids=saved_talk_ids,
        saved_exhibitor_ids=saved_exhibitor_ids
    )

# ----------------------------
# SELECT ACTIVE EVENT
# ----------------------------

@app.route("/events/set_current", methods=["POST"])
@login_required
def set_current_event():
    event_id = request.form.get("event_id")

    if not event_id:
        flash("Invalid event.")
        return redirect("/events")

    rows = db.execute("SELECT id, name FROM events WHERE id = ?", event_id)
    if len(rows) != 1:
        flash("Event not found.")
        return redirect("/events")

    # We save in session
    session["current_event_id"] = rows[0]["id"]
    session["current_event_name"] = rows[0]["name"]

    flash(f"Current event set to {rows[0]['name']}.")
    return redirect(url_for("event_detail", event_id=rows[0]["id"]))


# ----------------------------
# USER REGISTRATION
# ----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validations
        if not username:
            flash("Username required.")
            return redirect("/register")

        if not email:
            flash("Email required.")
            return redirect("/register")

        if not password:
            flash("Password required.")
            return redirect("/register")

        if password != confirmation:
            flash("Passwords do not match.")
            return redirect("/register")

        # Does it already exist?
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            username,
            email,
        )

        if len(existing) > 0:
            flash("Username or email already exists.")
            return redirect("/register")

        # Create user
        hashed = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (username, email, hash) VALUES (?, ?, ?)",
            username,
            email,
            hashed,
        )

        flash("Account created. You can now log in.")
        return redirect("/login")

    # GET
    return render_template("register.html")


# ----------------------------
# USER LOGIN
# ----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Username required.")
            return redirect("/login")

        if not password:
            flash("Password required.")
            return redirect("/login")

        # Search for user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username or password.")
            return redirect("/login")

        # Save session
        session["user_id"] = rows[0]["id"]
        session["is_admin"] = rows[0]["is_admin"]

        flash("Welcome back!")
        return redirect("/")

    # GET
    return render_template("login.html")


# ----------------------------
# LOGOUT
# ----------------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect("/")

# ----------------------------
# PROFILE
# ----------------------------

@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    user = db.execute("SELECT username, email, is_admin FROM users WHERE id = ?", user_id)

    if len(user) != 1:
        flash("User not found.")
        return redirect("/")

    return render_template("profile.html", user=user[0])

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        if session.get("is_admin") != 1:
            flash("You do not have permission to access the admin panel.")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Actualizar username y email."""
    user_id = session["user_id"]
    username = request.form.get("username")
    email = request.form.get("email")

    if not username or not email:
        flash("Username and email are required.")
        return redirect("/profile")

    # Verify that they are not being used by another user
    rows = db.execute(
        "SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?",
        username,
        email,
        user_id,
    )
    if len(rows) > 0:
        flash("Username or email already in use.")
        return redirect("/profile")

    db.execute(
        "UPDATE users SET username = ?, email = ? WHERE id = ?",
        username,
        email,
        user_id,
    )

    flash("Profile updated successfully.")
    return redirect("/profile")


@app.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    """Cambiar la contraseña del usuario."""
    user_id = session["user_id"]
    current = request.form.get("current_password")
    new = request.form.get("new_password")
    confirmation = request.form.get("confirmation")

    if not current or not new or not confirmation:
        flash("Please fill out all password fields.")
        return redirect("/profile")

    # Get current hash
    rows = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], current):
        flash("Current password is incorrect.")
        return redirect("/profile")

    if new != confirmation:
        flash("New passwords do not match.")
        return redirect("/profile")

    # Update hash
    new_hash = generate_password_hash(new)
    db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, user_id)

    flash("Password updated successfully.")
    return redirect("/profile")

# ----------------------------
# ADMIN DASHBOARD
# ----------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    total_users = db.execute("SELECT COUNT(*) AS count FROM users")[0]["count"]
    total_talks = db.execute("SELECT COUNT(*) AS count FROM talks")[0]["count"]
    total_exhibitors = db.execute("SELECT COUNT(*) AS count FROM exhibitors")[0]["count"]

    return render_template("admin_dashboard.html",
                           total_users=total_users,
                           total_talks=total_talks,
                           total_exhibitors=total_exhibitors)

# ----------------------------
# ADMIN - MANAGE TALKS
# ----------------------------

@app.route("/admin/charlas/delete/<int:talk_id>")
@admin_required
def delete_charla(talk_id):
    """Delete a talk from the database (admin only)."""
    db.execute("DELETE FROM talks WHERE id = ?", talk_id)
    flash("Talk deleted.")
    return redirect("/admin/charlas")


@app.route("/admin/charlas", methods=["GET", "POST"])
@admin_required
def admin_charlas():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        track = request.form.get("track")
        start = request.form.get("start_time")
        end = request.form.get("end_time")
        location = request.form.get("location")
        event_id = request.form.get("event_id")  # ⬅️ nuevo

        if not title:
            flash("Title required.")
            return redirect("/admin/charlas")

        if not event_id:
            flash("You must select an event.")
            return redirect("/admin/charlas")

        db.execute("""
            INSERT INTO talks (title, description, track, start_time, end_time, location, event_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, title, description, track, start, end, location, event_id)

        flash("Talk added successfully.")
        return redirect("/admin/charlas")

    # GET → load talks + events
    talks = db.execute("""
        SELECT talks.*, events.name AS event_name
        FROM talks
        LEFT JOIN events ON talks.event_id = events.id
        ORDER BY events.name, talks.start_time
    """)

    events = db.execute("SELECT id, name FROM events ORDER BY name")

    return render_template("admin_charlas.html",
                           talks=talks,
                           events=events)



# ----------------------------
# ADMIN - MANAGE EXHIBITORS
# ----------------------------

@app.route("/admin/expositores/delete/<int:exhibitor_id>")
@admin_required
def delete_expositor(exhibitor_id):
    """Delete an exhibitor from the database (admin only)."""
    db.execute("DELETE FROM exhibitors WHERE id = ?", exhibitor_id)
    flash("Exhibitor deleted.")
    return redirect("/admin/expositores")


@app.route("/admin/expositores", methods=["GET", "POST"])
@admin_required
def admin_expositores():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        sector = request.form.get("sector")
        stand = request.form.get("stand")
        event_id = request.form.get("event_id")

        if not name:
            flash("Name required.")
            return redirect("/admin/expositores")

        if not event_id:
            flash("You must select an event.")
            return redirect("/admin/expositores")

        db.execute("""
            INSERT INTO exhibitors (name, description, sector, stand, event_id)
            VALUES (?, ?, ?, ?, ?)
        """, name, description, sector, stand, event_id)

        flash("Exhibitor added.")
        return redirect("/admin/expositores")

    exhibitors = db.execute("""
        SELECT exhibitors.*, events.name AS event_name
        FROM exhibitors
        LEFT JOIN events ON exhibitors.event_id = events.id
        ORDER BY events.name, exhibitors.name
    """)

    events = db.execute("SELECT id, name FROM events ORDER BY name")

    return render_template("admin_expositores.html",
                           exhibitors=exhibitors,
                           events=events)

# ----------------------------
# ADMIN - MANAGE EVENTS
# ----------------------------

@app.route("/admin/events", methods=["GET", "POST"])
@admin_required
def admin_events():
    if request.method == "POST":
        name = request.form.get("name")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        location = request.form.get("location")
        description = request.form.get("description")

        if not name:
            flash("Event name is required.")
            return redirect("/admin/events")

        db.execute(
            """
            INSERT INTO events (name, start_date, end_date, location, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            name,
            start_date,
            end_date,
            location,
            description
        )

        flash("Event created successfully.")
        return redirect("/admin/events")

    # GET -> list events
    events = db.execute(
        "SELECT * FROM events ORDER BY start_date IS NULL, start_date"
    )

    return render_template("admin_events.html", events=events)



@app.route("/admin/events/delete/<int:event_id>")
@admin_required
def delete_event(event_id):
    # NOTE: this does not delete linked talks/speakers; for now.
    db.execute("DELETE FROM events WHERE id = ?", event_id)
    flash("Event deleted.")
    return redirect("/admin/events")


# ----------------------------
# RECOMMENDATIONS
# ----------------------------

@app.route("/recommendations")
@login_required
def recommendations():
    user_id = session["user_id"]

    # Active event (if any)
    current_event_id = session.get("current_event_id")
    current_event_name = session.get("current_event_name")

    conn = get_db_connection()
    cur = conn.cursor()

    # 1) User preferences based on their current schedule
    #    TRACKS of the talks they have already saved (from the active event, if any)
    if current_event_id:
        cur.execute("""
            SELECT t.track, COUNT(*) AS cnt
            FROM user_talks ut
            JOIN talks t ON ut.talk_id = t.id
            WHERE ut.user_id = ? AND t.event_id = ?
            GROUP BY t.track
        """, (user_id, current_event_id))
    else:
        cur.execute("""
            SELECT t.track, COUNT(*) AS cnt
            FROM user_talks ut
            JOIN talks t ON ut.talk_id = t.id
            WHERE ut.user_id = ?
            GROUP BY t.track
        """, (user_id,))
    track_counts = {row["track"]: row["cnt"] for row in cur.fetchall() if row["track"]}

    #    SECTORS of the exhibitors you already have saved (from the active event, if any)
    if current_event_id:
        cur.execute("""
            SELECT e.sector, COUNT(*) AS cnt
            FROM user_exhibitors ue
            JOIN exhibitors e ON ue.exhibitor_id = e.id
            WHERE ue.user_id = ? AND e.event_id = ?
            GROUP BY e.sector
        """, (user_id, current_event_id))
    else:
        cur.execute("""
            SELECT e.sector, COUNT(*) AS cnt
            FROM user_exhibitors ue
            JOIN exhibitors e ON ue.exhibitor_id = e.id
            WHERE ue.user_id = ?
            GROUP BY e.sector
        """, (user_id,))
    sector_counts = {row["sector"]: row["cnt"] for row in cur.fetchall() if row["sector"]}

    #2) Talk schedules already on the agenda -> to avoid overlaps
    if current_event_id:
        cur.execute("""
            SELECT t.start_time, t.end_time
            FROM user_talks ut
            JOIN talks t ON ut.talk_id = t.id
            WHERE ut.user_id = ? AND t.event_id = ?
        """, (user_id, current_event_id))
    else:
        cur.execute("""
            SELECT t.start_time, t.end_time
            FROM user_talks ut
            JOIN talks t ON ut.talk_id = t.id
            WHERE ut.user_id = ?
        """, (user_id,))

    user_times = []
    for row in cur.fetchall():
        s = parse_hhmm(row["start_time"])
        e = parse_hhmm(row["end_time"])
        if s and e:
            user_times.append((s, e))

    def overlaps(start, end, intervals):
        """True si [start, end] solapa con alguno de intervals."""
        for s2, e2 in intervals:
            if start < e2 and end > s2:
                return True
        return False

    #3) Talk IDs/speakers already on the agenda (all events)
    cur.execute("SELECT talk_id FROM user_talks WHERE user_id = ?", (user_id,))
    saved_talk_ids = {row["talk_id"] for row in cur.fetchall()}

    cur.execute("SELECT exhibitor_id FROM user_exhibitors WHERE user_id = ?", (user_id,))
    saved_exhibitor_ids = {row["exhibitor_id"] for row in cur.fetchall()}

    #4) Get all unsaved talks (only from the active event, if any)
    if current_event_id:
        cur.execute("SELECT * FROM talks WHERE event_id = ?", (current_event_id,))
    else:
        cur.execute("SELECT * FROM talks")
    talks_raw = cur.fetchall()

    recommended_talks = []
    for row in talks_raw:
        if row["id"] in saved_talk_ids:
            continue  # already on the agenda

        talk = dict(row)
        track = talk.get("track") or "Other"

        start = parse_hhmm(talk.get("start_time"))
        end = parse_hhmm(talk.get("end_time"))
        if start and end and user_times and overlaps(start, end, user_times):
            # Overlaps with something on the agenda
            continue

        # Base score
        score = 1

        # Bonus for favorite track
        if track in track_counts:
            score += 10 * track_counts[track]
            reason = f"Matches your interest in '{track}' talks."
        else:
            reason = "Good to discover a new track."

        talk["score"] = score
        talk["reason"] = reason
        recommended_talks.append(talk)

    recommended_talks.sort(key=lambda t: t["score"], reverse=True)

    #5) Get unsaved exhibitors (only from the active event, if any)
    if current_event_id:
        cur.execute("SELECT * FROM exhibitors WHERE event_id = ?", (current_event_id,))
    else:
        cur.execute("SELECT * FROM exhibitors")
    exhibitors_raw = cur.fetchall()

    recommended_exhibitors = []
    for row in exhibitors_raw:
        if row["id"] in saved_exhibitor_ids:
            continue

        exhibitor = dict(row)
        sector = exhibitor.get("sector") or "Other"

        score = 1
        if sector in sector_counts:
            score += 10 * sector_counts[sector]
            reason = f"Matches your interest in '{sector}' exhibitors."
        else:
            reason = "New sector to explore."

        exhibitor["score"] = score
        exhibitor["reason"] = reason
        recommended_exhibitors.append(exhibitor)

    recommended_exhibitors.sort(key=lambda e: e["score"], reverse=True)

    conn.close()

    return render_template(
        "recommendations.html",
        talks=recommended_talks,
        exhibitors=recommended_exhibitors,
        track_counts=track_counts,
        sector_counts=sector_counts,
        current_event_name=current_event_name,
    )


# ----------------------------
# AGENDA - VIEW AGENDA
# ----------------------------

@app.route("/agenda")
@login_required
def agenda():
    user_id = session["user_id"]
    current_event_id = session.get("current_event_id")
    current_event_name = session.get("current_event_name")

    if current_event_id:
        # Filter only talks from the event
        saved_talks = db.execute("""
            SELECT talks.id, talks.title, talks.description, talks.track,
                   talks.start_time, talks.end_time, talks.location
            FROM user_talks
            JOIN talks ON user_talks.talk_id = talks.id
            WHERE user_talks.user_id = ? AND talks.event_id = ?
            ORDER BY talks.start_time
        """, user_id, current_event_id)

        # Filter only exhibitors at the event
        saved_exhibitors = db.execute("""
            SELECT exhibitors.id, exhibitors.name, exhibitors.description,
                   exhibitors.sector, exhibitors.stand
            FROM user_exhibitors
            JOIN exhibitors ON user_exhibitors.exhibitor_id = exhibitors.id
            WHERE user_exhibitors.user_id = ? AND exhibitors.event_id = ?
        """, user_id, current_event_id)

    else:
        # If there is no active event → show everything
        saved_talks = db.execute("""
            SELECT talks.id, talks.title, talks.description, talks.track,
                   talks.start_time, talks.end_time, talks.location
            FROM user_talks
            JOIN talks ON user_talks.talk_id = talks.id
            WHERE user_talks.user_id = ?
            ORDER BY talks.start_time
        """, user_id)

        saved_exhibitors = db.execute("""
            SELECT exhibitors.id, exhibitors.name, exhibitors.description,
                   exhibitors.sector, exhibitors.stand
            FROM user_exhibitors
            JOIN exhibitors ON user_exhibitors.exhibitor_id = exhibitors.id
            WHERE user_exhibitors.user_id = ?
        """, user_id)

    return render_template(
        "agenda.html",
        talks=saved_talks,
        exhibitors=saved_exhibitors,
        current_event_name=current_event_name
    )


# ----------------------------
# AGENDA - CALENDAR VIEW
# ----------------------------

@app.route("/agenda/calendar")
@login_required
def agenda_calendar():
    user_id = session["user_id"]
    current_event_id = session.get("current_event_id")
    current_event_name = session.get("current_event_name")

    if current_event_id:
        talks = db.execute("""
            SELECT talks.id, talks.title, talks.track, talks.start_time, talks.end_time, talks.location
            FROM user_talks
            JOIN talks ON user_talks.talk_id = talks.id
            WHERE user_talks.user_id = ? AND talks.event_id = ?
            ORDER BY talks.start_time
        """, user_id, current_event_id)
    else:
        talks = db.execute("""
            SELECT talks.id, talks.title, talks.track, talks.start_time, talks.end_time, talks.location
            FROM user_talks
            JOIN talks ON user_talks.talk_id = talks.id
            WHERE user_talks.user_id = ?
            ORDER BY talks.start_time
        """, user_id)

    return render_template("agenda_calendar.html",
                           talks=talks,
                           current_event_name=current_event_name)



# ----------------------------
# ADD TALK TO AGENDA
# ----------------------------

@app.route("/agenda/add_talk", methods=["POST"])
@login_required
def add_talk():
    user_id = session["user_id"]
    talk_id = request.form.get("talk_id")

    #1) Validate that an ID is coming
    if not talk_id:
        flash("Invalid talk.")
        return redirect("/recommendations")

    #2) Verify that the chat exists in the database
    rows = db.execute("SELECT id FROM talks WHERE id = ?", talk_id)
    if len(rows) != 1:
        flash("This talk does not exist or has been removed.")
        return redirect("/recommendations")

    #3) Avoid duplicates in the user's calendar
    exists = db.execute(
        "SELECT id FROM user_talks WHERE user_id = ? AND talk_id = ?",
        user_id, talk_id
    )
    if len(exists) > 0:
        flash("Talk already in your agenda.")
        return redirect("/recommendations")

    #4) Insert into the relationship table
    db.execute(
        "INSERT INTO user_talks (user_id, talk_id) VALUES (?, ?)",
        user_id, talk_id
    )

    flash("Talk added to your agenda.")
    return redirect("/agenda")


# ----------------------------
# ADD EXHIBITOR TO AGENDA
# ----------------------------

@app.route("/agenda/add_exhibitor", methods=["POST"])
@login_required
def add_exhibitor():
    user_id = session["user_id"]
    exhibitor_id = request.form.get("exhibitor_id")

    #1) Validate that an ID is coming
    if not exhibitor_id:
        flash("Invalid exhibitor.")
        return redirect("/recommendations")

    #2) Verify that the display exists
    rows = db.execute("SELECT id FROM exhibitors WHERE id = ?", exhibitor_id)
    if len(rows) != 1:
        flash("This exhibitor does not exist or has been removed.")
        return redirect("/recommendations")

    #3) Avoid duplicates in the user's calendar
    exists = db.execute(
        "SELECT id FROM user_exhibitors WHERE user_id = ? AND exhibitor_id = ?",
        user_id, exhibitor_id
    )
    if len(exists) > 0:
        flash("Exhibitor already in your agenda.")
        return redirect("/recommendations")

    #4) Insert relationship
    db.execute(
        "INSERT INTO user_exhibitors (user_id, exhibitor_id) VALUES (?, ?)",
        user_id, exhibitor_id
    )

    flash("Exhibitor added to your agenda.")
    return redirect("/agenda")



# ----------------------------
# REMOVE CHAT FROM AGENDA
# ----------------------------

@app.route("/agenda/remove_talk/<int:talk_id>")
@login_required
def remove_talk(talk_id):
    user_id = session["user_id"]

    db.execute("DELETE FROM user_talks WHERE user_id = ? AND talk_id = ?",
               user_id, talk_id)

    flash("Talk removed from your agenda.")
    return redirect("/agenda")


# ----------------------------
# REMOVE EXHIBITOR FROM AGENDA
# ----------------------------

@app.route("/agenda/remove_exhibitor/<int:exhibitor_id>")
@login_required
def remove_exhibitor(exhibitor_id):
    user_id = session["user_id"]

    db.execute("DELETE FROM user_exhibitors WHERE user_id = ? AND exhibitor_id = ?",
               user_id, exhibitor_id)

    flash("Exhibitor removed from your agenda.")
    return redirect("/agenda")

# ----------------------------
# RUN SERVER
# ----------------------------

if __name__ == "__main__":
    app.run(debug=True)
