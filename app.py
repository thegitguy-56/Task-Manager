from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Team


app = Flask(__name__)

# ---- Config ----
app.config["SECRET_KEY"] = "change_this_in_production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
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


# DASHBOARD
@app.route("/dashboard")
@login_required
def dashboard():
    user_teams = None
    if current_user.role in ["admin", "manager"]:
        user_teams = Team.query.filter_by(manager_id=current_user.id).all()

    return render_template(
        "dashboard.html",
        user=current_user,
        user_teams=user_teams,
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


# ---- DB create + run ----
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
