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
# TeamOrbit - Team Task Manager

TeamOrbit is a web-based task manager built for small teams. It lets managers create teams, assign members, and track tasks, while team members can see and update the work assigned to them.

## Features

- User authentication (login, logout, registration)
- Role-based access:
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
  - Member completion statistics (for managers)
  - Recent activity feed

## Tech Stack

- Backend: Flask, Flask-Login, SQLAlchemy
- Database: PostgreSQL (Supabase), SQLite for local development
- Frontend: HTML, Jinja2 templates, Bootstrap
- Deployment: Vercel + Supabase PostgreSQL

## Getting Started (Local)

1. Clone the repository:

```bash
git clone https://github.com/thegitguy-56/Task-Manager.git
cd Task-Manager
```

2. Create and activate virtual environment:

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure local env in `.env`:

```text
SECRET_KEY=change-me-for-local-dev
DATABASE_URL=sqlite:///database.db
```

5. Run app:

```bash
flask --app app run
```

## Deploy on Vercel with Supabase

1. Create a Supabase project and copy the Transaction Pooler URL.
2. In Vercel, add environment variables:
   - DATABASE_URL
   - SECRET_KEY
   - INIT_DB_TOKEN
   - FLASK_ENV=production
3. Deploy this repository to Vercel.
4. Initialize the database once:

```text
https://your-app.vercel.app/init_db?token=your-init-db-token
```

5. Optional hardening: remove `INIT_DB_TOKEN` after initialization.

## Notes

- In production, `SECRET_KEY` and `DATABASE_URL` are required.
- For PostgreSQL URLs, `sslmode=require` is enforced automatically if missing.
- The init route is protected in production and requires `INIT_DB_TOKEN`.

