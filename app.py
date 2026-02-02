from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
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
from sqlalchemy import func, case

from models import db, User, Team, Task, Activity
from datetime import datetime, date
import os

from flask import Response
import csv
import io


app = Flask(__name__)

# ---- Config ----
app.config["SECRET_KEY"] = "change_this_in_production"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
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


def log_activity(action: str):
    if not current_user.is_authenticated:
        return
    entry = Activity(
        user_id=current_user.id,
        action=action,
        timestamp=datetime.utcnow(),
    )
    db.session.add(entry)
    # commit will be done by caller after their own changes


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


# PROFILE
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # Update name
        new_name = request.form.get("name")
        if not new_name:
            flash("Name cannot be empty")
            return redirect(url_for("profile"))

        current_user.name = new_name

        # Change password if fields filled
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if current_password or new_password or confirm_password:
            # All 3 must be present
            if not (current_password and new_password and confirm_password):
                flash("To change password, fill all password fields")
                return redirect(url_for("profile"))

            # Check current password
            if not check_password_hash(current_user.password_hash, current_password):
                flash("Current password is incorrect")
                return redirect(url_for("profile"))

            # Check new password match + basic length
            if new_password != confirm_password:
                flash("New passwords do not match")
                return redirect(url_for("profile"))
            if len(new_password) < 6:
                flash("New password must be at least 6 characters")
                return redirect(url_for("profile"))

            current_user.password_hash = generate_password_hash(
                new_password, method="pbkdf2:sha256"
            )

        db.session.commit()
        flash("Profile updated")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=current_user)


# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    # Teams managed by this user (for admin/manager)
    user_teams = []
    manager_teams = []
    selected_team_id = None

    # ---- ADMIN / MANAGER: teams they manage ----
    if current_user.role in ["admin", "manager"]:
        teams_q = Team.query.filter_by(manager_id=current_user.id).all()
        manager_teams = teams_q
        selected_team_id = request.args.get("team_id")

        # build enriched user_teams list for modal (same as before)
        for t in teams_q:
            manager_name = current_user.name

            teammates = (
                User.query
                .filter(User.team_id == t.id, User.id != t.manager_id)
                .all()
            )
            teammates_names = [u.name for u in teammates]
            teammates_str = ", ".join(teammates_names)

            user_teams.append({
                "team_name": t.team_name,
                "manager_name": manager_name,
                "teammates_str": teammates_str
            })

    # ---- MEMBER: show their single team in user_teams ----
    elif current_user.role == "member" and current_user.team_id:
        t = Team.query.get(current_user.team_id)
        if t:
            # manager of this team
            manager_user = User.query.get(t.manager_id) if t.manager_id else None
            manager_name = manager_user.name if manager_user else "—"

            # teammates = everyone in same team except current user
            teammates = (
                User.query
                .filter(User.team_id == t.id, User.id != current_user.id)
                .all()
            )
            teammates_names = [u.name for u in teammates]
            teammates_str = ", ".join(teammates_names)

            user_teams.append({
                "team_name": t.team_name,
                "manager_name": manager_name,
                "teammates_str": teammates_str
            })

    # Base task query, optionally filtered by team for managers/members
    task_query = Task.query
    if current_user.role in ["admin", "manager"] and selected_team_id:
        task_query = task_query.filter(Task.team_id == int(selected_team_id))
    elif current_user.role == "member" and current_user.team_id:
        task_query = task_query.filter(Task.team_id == current_user.team_id)

    total_tasks = task_query.count()
    completed_tasks = task_query.filter_by(status="completed").count()
    pending_tasks = task_query.filter_by(status="pending").count()
    in_progress_tasks = task_query.filter_by(status="in progress").count()

    progress_pct = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    # Per-user statistics (for admin/manager, optionally per team)
    user_stats = []
    if current_user.role in ["admin", "manager"]:
        user_query = User.query
        if selected_team_id:
            user_query = user_query.filter(User.team_id == int(selected_team_id))

        stats = (
            db.session.query(
                User.id,
                User.name,
                func.count(Task.id).label("total"),
                func.sum(
                    case(
                        (Task.status == "completed", 1),
                        else_=0,
                    )
                ).label("completed"),
            )
            .outerjoin(Task, Task.assigned_to == User.id)
            .filter(user_query.subquery().c.id == User.id)
            .group_by(User.id)
            .all()
        )

        for uid, name, total, completed in stats:
            total = total or 0
            completed = completed or 0
            pct = int(completed * 100 / total) if total else 0
            user_stats.append(
                {"name": name, "total": total, "completed": completed, "pct": pct}
            )

    # Team membership info for any logged-in user (you can keep or remove this,
    # it's not used by the new Your Teams pills but may be useful elsewhere)
    current_team = None
    teammates = []
    manager = None
    if current_user.team_id:
        current_team = Team.query.get(current_user.team_id)
        teammates = User.query.filter(
            User.team_id == current_user.team_id, User.id != current_user.id
        ).all()
        if current_team and current_team.manager_id:
            manager = User.query.get(current_team.manager_id)

    recent_activity = (
        Activity.query.order_by(Activity.timestamp.desc()).limit(10).all()
    )

    return render_template(
        "dashboard.html",
        user=current_user,
        user_teams=user_teams,         # now filled for members too
        manager_teams=manager_teams,
        selected_team_id=selected_team_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        progress_pct=progress_pct,
        user_stats=user_stats,
        current_team=current_team,
        teammates=teammates,
        manager=manager,
        recent_activity=recent_activity,
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

        # unreachable if forbidden, kept for clarity
    team_name = request.form.get("team_name")
    if not team_name:
        flash("Team name is required")
        return redirect(url_for("create_team_page"))

    new_team = Team(team_name=team_name, manager_id=current_user.id)
    db.session.add(new_team)
    db.session.commit()

    flash("Team created successfully")
    return redirect(url_for("dashboard"))


@app.route("/manage_teams", methods=["GET", "POST"])
@login_required
def manage_teams():
    if current_user.role not in ["admin", "manager"]:
        abort(403)

    # Teams this manager/admin owns
    teams = Team.query.filter_by(manager_id=current_user.id).all()

    selected_team_id = request.args.get("team_id") or request.form.get("team_id")
    selected_team = None
    team_members = []
    other_users = []

    if selected_team_id:
        selected_team = Team.query.get(int(selected_team_id))
        if selected_team and selected_team.manager_id != current_user.id:
            abort(403)

        if selected_team:
            team_members = User.query.filter(User.team_id == selected_team.id).all()
            other_users = User.query.filter(
                (User.team_id.is_(None)) | (User.team_id != selected_team.id)
            ).all()

    # Handle add/remove actions
    if request.method == "POST" and selected_team:
        action = request.form.get("action")
        user_id = request.form.get("user_id")
        if user_id:
            user = User.query.get(int(user_id))
        else:
            user = None

        if action == "add" and user:
            user.team_id = selected_team.id
            db.session.commit()
            flash(f"Added {user.name} to team {selected_team.team_name}")
        elif action == "remove" and user:
            user.team_id = None
            db.session.commit()
            flash(f"Removed {user.name} from team {selected_team.team_name}")

        return redirect(url_for("manage_teams", team_id=selected_team.id))

    return render_template(
        "manage_teams.html",
        teams=teams,
        selected_team=selected_team,
        team_members=team_members,
        other_users=other_users,
    )
@app.route("/delete_team/<int:team_id>", methods=["POST"])
@login_required
def delete_team(team_id):
    if current_user.role not in ["admin", "manager"]:
        abort(403)

    team = Team.query.get_or_404(team_id)

    # Only allow deleting teams owned by this manager/admin
    if team.manager_id != current_user.id:
        abort(403)

    # Detach users from this team
    members = User.query.filter(User.team_id == team.id).all()
    for u in members:
        u.team_id = None

    db.session.delete(team)
    db.session.commit()

    flash(f"Team {team.team_name} deleted")
    return redirect(url_for("manage_teams"))

@app.route("/init_db")
def init_db():
    with app.app_context():
        db.create_all()
    return "Database initialized"


# ---------- TASKS ----------

@app.route("/tasks")
@login_required
def tasks():
    view = request.args.get("view", "my")  # 'my' or 'all'
    status_filter = request.args.get("status", "")
    priority_filter = request.args.get("priority", "")
    search = request.args.get("search", "")
    sort = request.args.get("sort", "end_date")
    team_id = request.args.get("team_id")  # for admin/manager

    # Force members to "my" view
    if current_user.role == "member":
        view = "my"

    query = Task.query

    # Team filter
    if current_user.role == "member":
        # members only see tasks in their own team
        query = query.filter(Task.team_id == current_user.team_id)
        team_id = current_user.team_id
    else:
        if team_id:
            query = query.filter(Task.team_id == int(team_id))

    # My vs All
    if view == "my" or current_user.role == "member":
        query = query.filter(Task.assigned_to == current_user.id)

    # Filters
    if status_filter:
        query = query.filter(Task.status == status_filter)
    if priority_filter:
        query = query.filter(Task.priority == priority_filter)
    if search:
        query = query.filter(Task.task_name.ilike(f"%{search}%"))

    # Sort
    if sort == "end_date":
        query = query.order_by(Task.end_date.asc())
    elif sort == "priority":
        priority_order = case(
            (Task.priority == "High", 1),
            (Task.priority == "Medium", 2),
            (Task.priority == "Low", 3),
            else_=4,
        )
        query = query.order_by(priority_order, Task.end_date.asc())

    all_tasks = query.all()
    users = User.query.all()
    today = date.today()

    # Teams for manager/admin dropdown
    manager_teams = []
    if current_user.role in ["admin", "manager"]:
        manager_teams = Team.query.filter_by(manager_id=current_user.id).all()

    return render_template(
        "tasks.html",
        tasks=all_tasks,
        users=users,
        today=today,
        view=view,
        status_filter=status_filter,
        priority_filter=priority_filter,
        search=search,
        sort=sort,
        team_id=team_id,
        manager_teams=manager_teams,
    )


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

    # Members can only assign tasks to themselves
    if current_user.role == "member" and int(assigned_to) != current_user.id:
        flash("You can only create tasks assigned to yourself")
        return redirect(url_for("tasks"))

    # Determine team for this task
    team_id = None
    if current_user.role == "member":
        # member’s tasks always in their own team
        team_id = current_user.team_id
    else:
        # admin/manager chooses from form (we’ll add the field next)
        team_id_str = request.form.get("team_id")
        if team_id_str:
            team_id = int(team_id_str)

    if not team_id:
        flash("Please select a team for this task")
        return redirect(url_for("tasks"))

    start_date = (
        datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if start_date_str
        else None
    )
    end_date = (
        datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
    )

    if start_date and end_date and end_date < start_date:
        flash("End date cannot be before start date")
        return redirect(url_for("tasks"))

    new_task = Task(
        task_name=task_name,
        description=description,
        assigned_to=int(assigned_to),
        start_date=start_date,
        end_date=end_date,
        status="pending",
        priority=priority,
        team_id=team_id,
    )
    db.session.add(new_task)
    log_activity(f"created task '{task_name}'")
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

    old_status = task.status
    task.status = new_status
    log_activity(f"changed status of task '{task.task_name}' from {old_status} to {new_status}")
    db.session.commit()

    flash("Task status updated")
    return redirect(url_for("tasks"))


# ----- EDIT / DELETE TASKS -----

@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Simple permission: admin/manager or assignee can edit
    if current_user.role not in ["admin", "manager"] and current_user.id != task.assigned_to:
        abort(403)

    users = User.query.all()

    if request.method == "POST":
        task.task_name = request.form.get("task_name")
        task.description = request.form.get("description")
        assigned_to = request.form.get("assigned_to")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        task.priority = request.form.get("priority")

        if not task.task_name or not assigned_to:
            flash("Task name and assigned user are required")
            return redirect(url_for("edit_task", task_id=task.id))

        task.assigned_to = int(assigned_to)

        task.start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        task.end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date()
            if end_date_str
            else None
        )

        if task.start_date and task.end_date and task.end_date < task.start_date:
            flash("End date cannot be before start date")
            return redirect(url_for("edit_task", task_id=task.id))

        log_activity(f"edited task '{task.task_name}'")
        db.session.commit()
        flash("Task updated")
        return redirect(url_for("tasks"))

    return render_template("edit_task.html", task=task, users=users)


@app.route("/delete_task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if current_user.role not in ["admin", "manager"] and current_user.id != task.assigned_to:
        abort(403)

    log_activity(f"deleted task '{task.task_name}'")
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted")
    return redirect(url_for("tasks"))

@app.route("/reports")
@login_required
def reports():
    if current_user.role not in ["admin", "manager"]:
        abort(403)

    team_id = request.args.get("team_id")

    query = Task.query
    if team_id:
        query = query.filter(Task.team_id == int(team_id))

    total = query.count()
    pending = query.filter_by(status="pending").count()
    in_progress = query.filter_by(status="in progress").count()
    completed = query.filter_by(status="completed").count()

    high = query.filter_by(priority="High").count()
    medium = query.filter_by(priority="Medium").count()
    low = query.filter_by(priority="Low").count()

    # teams for dropdown (only teams this manager/admin owns)
    manager_teams = Team.query.filter_by(manager_id=current_user.id).all()

    return render_template(
        "reports.html",
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        high=high,
        medium=medium,
        low=low,
        team_id=team_id,
        manager_teams=manager_teams,
    )


@app.route("/reports/export")
@login_required
def export_reports_csv():
    if current_user.role not in ["admin", "manager"]:
        abort(403)

    tasks = Task.query.order_by(Task.end_date.asc()).all()
    users = {u.id: u.name for u in User.query.all()}

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        [
            "ID",
            "Task Name",
            "Description",
            "Assigned To",
            "Start Date",
            "End Date",
            "Status",
            "Priority",
        ]
    )

    for t in tasks:
        writer.writerow(
            [
                t.id,
                t.task_name,
                (t.description or "").replace("\n", " "),
                users.get(t.assigned_to, ""),
                t.start_date or "",
                t.end_date or "",
                t.status,
                t.priority or "",
            ]
        )

    csv_data = output.getvalue()
    output.close()

    response = Response(csv_data, mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=tasks_report.csv"
    return response

# ---- DB create + run ----
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
