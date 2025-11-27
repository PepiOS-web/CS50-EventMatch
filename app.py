from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_session import Session
from cs50 import SQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from datetime import datetime


# ----------------------------
# CONFIGURACIÓN BÁSICA
# ----------------------------

app = Flask(__name__)

# Clave secreta para sesiones
app.config["SECRET_KEY"] = "dev-secret-key-change-later"

# Configuración de sesión estilo CS50 Finance
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Conexión a la base de datos SQLite
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
# DECORADOR login_required
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
# RUTA PRINCIPAL
# ----------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ----------------------------
# REGISTRO DE USUARIO
# ----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validaciones
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

        # ¿Ya existe?
        existing = db.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            username,
            email,
        )

        if len(existing) > 0:
            flash("Username or email already exists.")
            return redirect("/register")

        # Crear usuario
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
# LOGIN DE USUARIO
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

        # Buscar usuario
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username or password.")
            return redirect("/login")

        # Guardar sesión
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

    # Comprobar que no estén usados por otro usuario
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

    # Obtener hash actual
    rows = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], current):
        flash("Current password is incorrect.")
        return redirect("/profile")

    if new != confirmation:
        flash("New passwords do not match.")
        return redirect("/profile")

    # Actualizar hash
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

        if not title:
            flash("Title required.")
            return redirect("/admin/charlas")

        db.execute("""
            INSERT INTO talks (title, description, track, start_time, end_time, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, title, description, track, start, end, location)

        flash("Talk added successfully.")
        return redirect("/admin/charlas")

    # GET
    talks = db.execute("SELECT * FROM talks")
    return render_template("admin_charlas.html", talks=talks)


@app.route("/admin/charlas/delete/<int:talk_id>")
@admin_required
def delete_charla(talk_id):
    db.execute("DELETE FROM talks WHERE id = ?", talk_id)
    flash("Talk deleted.")
    return redirect("/admin/charlas")

# ----------------------------
# ADMIN - MANAGE EXHIBITORS
# ----------------------------

@app.route("/admin/expositores", methods=["GET", "POST"])
@admin_required
def admin_expositores():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        sector = request.form.get("sector")
        stand = request.form.get("stand")

        if not name:
            flash("Name required.")
            return redirect("/admin/expositores")

        db.execute("""
            INSERT INTO exhibitors (name, description, sector, stand)
            VALUES (?, ?, ?, ?)
        """, name, description, sector, stand)

        flash("Exhibitor added.")
        return redirect("/admin/expositores")

    exhibitors = db.execute("SELECT * FROM exhibitors")
    return render_template("admin_expositores.html", exhibitors=exhibitors)


@app.route("/admin/expositores/delete/<int:exhibitor_id>")
@admin_required
def delete_expositor(exhibitor_id):
    db.execute("DELETE FROM exhibitors WHERE id = ?", exhibitor_id)
    flash("Exhibitor deleted.")
    return redirect("/admin/expositores")



# ----------------------------
# RECOMMENDATIONS
# ----------------------------

@app.route("/recommendations")
@login_required
def recommendations():
    user_id = session["user_id"]
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Preferencias del usuario basadas en su agenda actual
    #    Tracks de las charlas que ya tiene guardadas
    cur.execute("""
        SELECT t.track, COUNT(*) AS cnt
        FROM user_talks ut
        JOIN talks t ON ut.talk_id = t.id
        WHERE ut.user_id = ?
        GROUP BY t.track
    """, (user_id,))
    track_counts = {row["track"]: row["cnt"] for row in cur.fetchall() if row["track"]}

    #    Sectores de los expositores que ya tiene guardados
    cur.execute("""
        SELECT e.sector, COUNT(*) AS cnt
        FROM user_exhibitors ue
        JOIN exhibitors e ON ue.exhibitor_id = e.id
        WHERE ue.user_id = ?
        GROUP BY e.sector
    """, (user_id,))
    sector_counts = {row["sector"]: row["cnt"] for row in cur.fetchall() if row["sector"]}

    # 2) Horarios de charlas ya en agenda → para evitar solapamientos
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

    # 3) Charla ya en agenda → para excluirlas de las recomendaciones
    cur.execute("SELECT talk_id FROM user_talks WHERE user_id = ?", (user_id,))
    saved_talk_ids = {row["talk_id"] for row in cur.fetchall()}

    cur.execute("SELECT exhibitor_id FROM user_exhibitors WHERE user_id = ?", (user_id,))
    saved_exhibitor_ids = {row["exhibitor_id"] for row in cur.fetchall()}

    # 4) Obtener todas las charlas NO guardadas
    cur.execute("SELECT * FROM talks")
    talks_raw = cur.fetchall()

    recommended_talks = []
    for row in talks_raw:
        if row["id"] in saved_talk_ids:
            continue  # ya está en la agenda, no la recomendamos

        talk = dict(row)
        track = talk.get("track") or "Other"

        # Si tenemos horario y el usuario ya tiene charlas, evitamos solapamientos
        start = parse_hhmm(talk.get("start_time"))
        end = parse_hhmm(talk.get("end_time"))
        if start and end and user_times and overlaps(start, end, user_times):
            # Se solapa con algo de la agenda → no recomendar
            continue

        # puntuación básica
        score = 1

        # bonus si el track coincide con los que ya tiene el usuario
        if track in track_counts:
            score += 10 * track_counts[track]
            reason = f"Matches your interest in '{track}' talks."
        else:
            reason = "Good to discover a new track."

        talk["score"] = score
        talk["reason"] = reason
        recommended_talks.append(talk)

    # ordenar por puntuación (de mayor a menor)
    recommended_talks.sort(key=lambda t: t["score"], reverse=True)

    # 5) Obtener expositores NO guardados
    cur.execute("SELECT * FROM exhibitors")
    exhibitors_raw = cur.fetchall()

    recommended_exhibitors = []
    for row in exhibitors_raw:
        if row["id"] in saved_exhibitor_ids:
            continue  # ya está en la agenda

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
    )

# ----------------------------
# AGENDA - VER AGENDA
# ----------------------------

@app.route("/agenda")
@login_required
def agenda():
    user_id = session["user_id"]

    # Obtener charlas guardadas
    saved_talks = db.execute("""
        SELECT talks.id, talks.title, talks.description, talks.track,
               talks.start_time, talks.end_time, talks.location
        FROM user_talks
        JOIN talks ON user_talks.talk_id = talks.id
        WHERE user_talks.user_id = ?
    """, user_id)

    # Obtener expositores guardados
    saved_exhibitors = db.execute("""
        SELECT exhibitors.id, exhibitors.name, exhibitors.description,
               exhibitors.sector, exhibitors.stand
        FROM user_exhibitors
        JOIN exhibitors ON user_exhibitors.exhibitor_id = exhibitors.id
        WHERE user_exhibitors.user_id = ?
    """, user_id)

    return render_template("agenda.html",
                           talks=saved_talks,
                           exhibitors=saved_exhibitors)

# ----------------------------
# AÑADIR CHARLA A LA AGENDA
# ----------------------------

@app.route("/agenda/add_talk", methods=["POST"])
@login_required
def add_talk():
    talk_id = request.form.get("talk_id")
    user_id = session["user_id"]

    if not talk_id:
        flash("Invalid talk.")
        return redirect("/recommendations")

    # Evitar duplicados
    exists = db.execute(
        "SELECT id FROM user_talks WHERE user_id = ? AND talk_id = ?",
        user_id, talk_id
    )

    if len(exists) > 0:
        flash("Talk already in your agenda.")
        return redirect("/recommendations")

    # Insertar
    db.execute(
        "INSERT INTO user_talks (user_id, talk_id) VALUES (?, ?)",
        user_id, talk_id
    )

    flash("Talk added to your agenda.")
    return redirect("/agenda")


# ----------------------------
# AÑADIR EXPOSITOR A LA AGENDA
# ----------------------------

@app.route("/agenda/add_exhibitor", methods=["POST"])
@login_required
def add_exhibitor():
    exhibitor_id = request.form.get("exhibitor_id")
    user_id = session["user_id"]

    if not exhibitor_id:
        flash("Invalid exhibitor.")
        return redirect("/recommendations")

    # Evitar duplicados
    exists = db.execute(
        "SELECT id FROM user_exhibitors WHERE user_id = ? AND exhibitor_id = ?",
        user_id, exhibitor_id
    )

    if len(exists) > 0:
        flash("Exhibitor already in your agenda.")
        return redirect("/recommendations")

    # Insertar
    db.execute(
        "INSERT INTO user_exhibitors (user_id, exhibitor_id) VALUES (?, ?)",
        user_id, exhibitor_id
    )

    flash("Exhibitor added to your agenda.")
    return redirect("/agenda")


# ----------------------------
# ELIMINAR CHARLA DE LA AGENDA
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
# ELIMINAR EXPOSITOR DE LA AGENDA
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
# EJECUTAR SERVIDOR
# ----------------------------

if __name__ == "__main__":
    app.run(debug=True)
