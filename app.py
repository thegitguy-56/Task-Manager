from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Team, Task
from datetime import datetime
import os


app = Flask(__name__)

# ---- Config ----
app.config["SECRET_KEY"] = "change_this_in_production"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
# For some providers, postgres URL starts with postgres:// which SQLAlchemy dislikes
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---- Init DB ----
db.init_app(app)

# ---- Login Manager ----
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- ROUTES ----------

@app.route("/")
def home():
    return redirect(url_for("login"))


# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "member")

        if not name or not email or not password:
            flash("All fields are required")
            return redirect(url_for("register"))

        # check duplicate email
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(
            name=name,
            email=email,
            password_hash=hashed,
            role=role,
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password")
            return redirect(url_for("login"))

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out")
    return redirect(url_for("login"))

@app.route("/init_db")
def init_db():
    with app.app_context():
        db.create_all()
    return "Database initialized"

# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    user_teams = None
    if current_user.role in ["admin", "manager"]:
        user_teams = Team.query.filter_by(manager_id=current_user.id).all()

    # ---- Module 4: progress metrics ----
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status="completed").count()

    if total_tasks > 0:
        progress_pct = round((completed_tasks / total_tasks) * 100)
    else:
        progress_pct = 0

    return render_template(
        "dashboard.html",
        user=current_user,
        user_teams=user_teams,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        progress_pct=progress_pct,
    )



# TEAM CREATION (admin/manager only)
@app.route("/create_team_page")
@login_required
def create_team_page():
    if current_user.role not in ["admin", "manager"]:
        abort(403)
    return render_template("create_team.html")


@app.route("/create_team", methods=["POST"])
@login_required
def create_team():
    if current_user.role not in ["admin", "manager"]:
        abort(403)

    team_name = request.form.get("team_name")
    if not team_name:
        flash("Team name is required")
        return redirect(url_for("create_team_page"))

    new_team = Team(team_name=team_name, manager_id=current_user.id)
    db.session.add(new_team)
    db.session.commit()

    flash("Team created successfully")
    return redirect(url_for("dashboard"))

# ---------- TASKS (Module 3) ----------

@app.route("/tasks")
@login_required
def tasks():
    # For now, show all tasks. Later you can filter by team/assigned user.
    all_tasks = Task.query.all()
    users = User.query.all()  # used for "Assigned To" dropdown
    return render_template("tasks.html", tasks=all_tasks, users=users)


@app.route("/create_task", methods=["POST"])
@login_required
def create_task():
    task_name = request.form.get("task_name")
    description = request.form.get("description")
    assigned_to = request.form.get("assigned_to")
    start_date_str = request.form.get("start_date")
    end_date_str = request.form.get("end_date")
    priority = request.form.get("priority")

    if not task_name or not assigned_to:
        flash("Task name and assigned user are required")
        return redirect(url_for("tasks"))

    # convert dates from string (YYYY-MM-DD) to date objects
    start_date = None
    end_date = None
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    new_task = Task(
        task_name=task_name,
        description=description,
        assigned_to=int(assigned_to),
        start_date=start_date,
        end_date=end_date,
        status="pending",
        priority=priority,
    )
    db.session.add(new_task)
    db.session.commit()

    flash("Task created successfully")
    return redirect(url_for("tasks"))


@app.route("/update_status/<int:task_id>", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)

    new_status = request.form.get("status")
    if new_status not in ["pending", "in progress", "completed"]:
        flash("Invalid status")
        return redirect(url_for("tasks"))

    # (Basic rule: any logged-in user can update; you can restrict later)
    task.status = new_status
    db.session.commit()

    flash("Task status updated")
    return redirect(url_for("tasks"))

# ---- DB create + run ----
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
