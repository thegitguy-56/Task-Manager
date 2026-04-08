# TeamOrbit Task Manager

## Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
flask --app app run
```

## Deploy on Vercel with Supabase

1. Create a Supabase project and copy the Transaction Pooler URL.
2. Set these environment variables in Vercel:
	- DATABASE_URL
	- SECRET_KEY
	- INIT_DB_TOKEN
	- FLASK_ENV=production
3. Deploy this repository to Vercel.
4. Initialize the database once:

```text
https://your-app.vercel.app/init_db?token=your-init-db-token
```

5. Remove INIT_DB_TOKEN from Vercel after initialization if you do not need it anymore.

### Notes

- In production, SECRET_KEY and DATABASE_URL are required.
- For PostgreSQL URLs, sslmode=require is enforced automatically if missing.
- The init route is protected in production and requires INIT_DB_TOKEN.
