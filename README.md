***

# TeamOrbit – Team Task Manager

TeamOrbit is a web‑based task manager built for small teams. It lets managers create teams, assign members, and track tasks, while team members can see and update the work assigned to them.

This project was developed as a capstone to practice full‑stack development with Flask, PostgreSQL, and modern UI components.

***

## Features

- User authentication (login, logout, registration)
- Role‑based access:
  - Admin / Manager: manage teams and tasks
  - Member: view and update their own tasks
- Team management:
  - Create and delete teams
  - Add or remove users from a team
- Task management:
  - Create tasks for a specific team and assignee
  - Set priority (Low, Medium, High)
  - Track status (Pending, In Progress, Completed)
  - Filter and search tasks by team, status, priority, and text
- Dashboard:
  - Overall task progress
  - Tasks‑by‑status chart
  - Member completion statistics (for managers)
  - Recent activity feed
- Responsive UI using Bootstrap

***

## Tech Stack

- **Backend:** Flask, Flask‑Login, SQLAlchemy
- **Database:** PostgreSQL (Render), SQLite for local development
- **Frontend:** HTML, Jinja2 templates, Bootstrap, a bit of vanilla JavaScript
- **Deployment:** Render Web Service + Render PostgreSQL

***

## Getting Started (Local)

### 1. Clone the repository

```bash
git clone https://github.com/thegitguy-56/Task-Manager.git
cd Task-Manager
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# macOS / Linux
# source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file (or set env vars manually):

```text
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=some-secret-key
# For local dev you can use SQLite:
DATABASE_URL=sqlite:///database.db
```

By default, the app falls back to `sqlite:///database.db` if `DATABASE_URL` is not set.

### 5. Initialize the database

Open a Python shell with the virtual environment active:

```bash
python
```

Then:

```python
from app import app, db
app.app_context().push()
db.create_all()
exit()
```

This creates the tables for users, teams, tasks, and activities.

### 6. Run the app

```bash
flask run
```

Visit `http://127.0.0.1:5000` in your browser.

***

## Deployment (Render)

At a high level, deployment works like this:

1. Push your code to GitHub.
2. Create a **Render PostgreSQL** instance and copy the `DATABASE_URL`.
3. Create a **Render Web Service**:
   - Connect it to your GitHub repo.
   - Set the build and start command (for example: `pip install -r requirements.txt` and `gunicorn app:app`).
   - Add environment variables, especially `DATABASE_URL` and `SECRET_KEY`.
4. From your local machine, point `DATABASE_URL` to the Render Postgres URL and run `db.create_all()` once so the remote DB gets the correct schema.
5. Enable automatic deploys on push to `main` if you want continuous deployment.

***

## Project Structure (simplified)

```text
.
├── app.py              # Flask app, routes, configuration
├── models.py           # SQLAlchemy models
├── templates/          # Jinja2 templates (dashboard, tasks, teams, auth)
├── static/
│   ├── css/            # Custom styles
│   └── js/             # Small JS files (charts, modal logic)
├── requirements.txt
└── README.md
```

***

## What I Learned

Working on TeamOrbit helped me practice:

- Designing relational models for users, teams, and tasks
- Implementing role‑based permissions in Flask
- Writing filtered SQLAlchemy queries for dashboards and reports
- Handling schema changes safely when using PostgreSQL in production
- Deploying a Python web app to Render and wiring it to a managed database

***

## Future Improvements

If I continue this project, possible enhancements include:

- Alembic migrations for smoother schema changes
- Email notifications when tasks are assigned or completed
- File attachments or comments on tasks
- More detailed reporting (per‑team burndown charts, export to CSV/PDF)

***
