# TeamOrbit Task Manager

TeamOrbit is a Flask-based team task management web app built for small teams. It supports role-based access, team ownership, task assignment, progress tracking, and report export.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Run the App](#run-the-app)
- [Usage Guide](#usage-guide)
- [Deployment (Vercel + Supabase)](#deployment-vercel--supabase)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)

## Overview

This project provides:

- Authentication with register, login, logout, and profile update
- Role-based behavior for admin/manager/member
- Team creation and team member management
- Task creation, filtering, editing, deletion, and status updates
- Dashboard metrics and recent activity
- Reports view with CSV export

## Features

### Authentication and Profiles

- User registration with hashed passwords
- Login/logout via Flask-Login
- Profile update:
  - change display name
  - optional password change with current password validation

### Roles and Permissions

- `admin` and `manager` can:
  - create and delete teams they own
  - manage team membership
  - create and manage team tasks
  - access analytics and reports
- `member` can:
  - view team-related dashboard/task data
  - create tasks assigned to themselves
  - update task status

### Team Management

- Create teams
- View owned teams
- Add/remove users from selected teams
- Delete owned teams (members are detached from the deleted team)

### Task Management

- Create tasks with:
  - title
  - description
  - assignee
  - start/end dates
  - priority (`Low`, `Medium`, `High`)
  - team
- Validate date range (end date cannot be before start date)
- Filter tasks by:
  - view mode (`my` or `all`)
  - status
  - priority
  - search text
  - team (for admin/manager)
- Sort tasks by due date or priority
- Edit/delete tasks (permission-based)
- Update status (`pending`, `in progress`, `completed`)

### Dashboard and Reporting

- Task counts by status
- Completion percentage
- Per-user completion stats (admin/manager)
- Recent activity stream
- Reports page with status and priority breakdowns
- Export tasks to CSV (`/reports/export`)

## Tech Stack

- Backend: Flask, Flask-Login, Flask-SQLAlchemy
- ORM/DB: SQLAlchemy, PostgreSQL (production), SQLite (local default)
- Frontend: Jinja2 templates, Bootstrap, custom CSS
- Server (production): Gunicorn
- Deployment target: Vercel

## Project Structure

```text
app.py                    # Flask app, routes, config
models.py                 # SQLAlchemy models
requirements.txt          # Python dependencies
vercel.json               # Vercel runtime config
project_summary.txt       # high-level project notes

templates/                # Jinja templates
  base.html
  dashboard.html
  tasks.html
  reports.html
  ...
  partials/
    _create_task_modal.html

static/                   # CSS and static assets
  style.css
  bootstrap-theme.css

instance/                 # local instance files (if generated)
```

## Data Model

The app defines four main tables in `models.py`:

- `User`
  - `id`, `name`, `email`, `password_hash`, `role`, `team_id`
- `Team`
  - `id`, `team_name`, `manager_id`
- `Task`
  - `id`, `task_name`, `description`, `assigned_to`, `team_id`, `start_date`, `end_date`, `status`, `priority`
- `Activity`
  - `id`, `user_id`, `action`, `timestamp`

## Environment Variables

Create a `.env` file in the project root.

Required in production:

- `SECRET_KEY`
- `DATABASE_URL`

Optional (but recommended for protected DB initialization):

- `INIT_DB_TOKEN`

Behavior notes from app config:

- Production mode is detected when `FLASK_ENV=production` or `VERCEL=1`
- In production:
  - app raises an error if `SECRET_KEY` is not set
  - app raises an error if `DATABASE_URL` is not set
- If a PostgreSQL URL is used and `sslmode` is missing, `sslmode=require` is appended automatically

Example local `.env`:

```dotenv
SECRET_KEY=change-me-for-local-dev
DATABASE_URL=sqlite:///database.db
```

## Local Setup

1. Clone the repository:

```bash
git clone https://github.com/thegitguy-56/Task-Manager.git
cd Task-Manager
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create/update `.env` with local values.

## Run the App

Option 1 (Flask CLI):

```bash
flask --app app run
```

Option 2 (direct execution):

```bash
python app.py
```

Default local URL:

- `http://127.0.0.1:5000`

## Usage Guide

1. Register users with appropriate roles (`admin`, `manager`, `member`)
2. Login as admin/manager and create one or more teams
3. Add members to teams from Manage Teams
4. Create tasks and assign them to users
5. Track progress from Dashboard and Tasks pages
6. Use Reports for status/priority summaries and CSV export

Important role behavior:

- Members are forced to `my` task view and can only create tasks assigned to themselves
- Managers/admins only manage teams they own

## Deployment (Vercel + Supabase)

1. Create a PostgreSQL database (for example, Supabase)
2. Add environment variables in Vercel:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `INIT_DB_TOKEN`
   - `FLASK_ENV=production`
3. Deploy the repository to Vercel
4. Initialize tables one time:

```text
https://<your-app-domain>/init_db?token=<your-init-db-token>
```

5. After initialization, rotate or remove `INIT_DB_TOKEN` if not needed

## Security Notes

- Never commit real credentials or production secrets to version control
- Use a strong random `SECRET_KEY` in production
- Restrict who can access the `/init_db` route by using `INIT_DB_TOKEN`
- Prefer least-privilege database credentials

## Troubleshooting

- App fails at startup in production:
  - confirm `SECRET_KEY` and `DATABASE_URL` are set
- DB connection issues with PostgreSQL:
  - verify host/user/password/db name
  - ensure network access and valid SSL settings
- Tables missing:
  - call `/init_db` with valid token in production
  - or run locally with `python app.py` (creates tables on startup)
- Task/team visibility seems wrong:
  - verify user role and `team_id` assignments

---
