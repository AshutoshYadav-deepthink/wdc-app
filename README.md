# WDC App — Women Development Cell

College web application for the Women Development Cell.
**Stack (locked):** Python · FastAPI · Firebase Admin SDK · Jinja2 templates · SQLite/JSON fallback.

The README in your master package said *"Python, FastAPI, Firebase"* — this project implements exactly that stack, with a built-in local JSON fallback so the app runs immediately without Firebase credentials (perfect for college demos).

---

## 1. Features

### Public (no login)
- Public WDC dashboard at `/` — opens first (per requirements)
- Browse upcoming published events
- View important women's observance dates
- Hero + about section

### Student (login or sign-up)
- Combined Student Login + Sign Up page at `/login`
- Private student dashboard at `/student` with:
  - Available events + one-click registration
  - My registrations (cancel option)
  - My attendance records
  - In-app notifications (read/unread)

### Admin / Staff
- Separate admin login (same `/login` page, "Admin / Staff" tab)
- Admin dashboard at `/admin` with:
  - Events CRUD (create / edit / delete / archive)
  - Attendance marking per event
  - Send notifications (in-app / email / push) — audience: all, by department, by class, by event
  - User management + role change (Super Admin only for CHANGE_USER_ROLE)
  - Reports dashboard (totals + per-event stats)

### Roles & Permissions (from `roles_permissions.json`)
- **Super Admin** — all 10 permissions; can change anyone's role
- **Admin** — manage events, speakers, registrations, attendance, notifications, reports, users
- **Coordinator** — events, registrations, attendance, notifications, reports
- **Staff** — attendance, reports
- **Student** — view public content only

### Departments & Classes
- Departments: BSc IT, BMS, BAF, BCom
- Classes: FY/SY/TY for each department

---

## 2. Project Structure

```
wdc_app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + page routes
│   ├── config.py            # Settings (env vars)
│   ├── schemas.py           # Pydantic models
│   ├── security.py          # Password hash + JWT
│   ├── auth.py              # Auth dependencies (get_current_user, require_role, require_permission)
│   ├── seed.py              # Seed data loader (auto-runs on first start)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/auth/* (signup, login, admin login, logout, me)
│   │   ├── public.py        # /api/events, /api/women-dates, /api/speakers
│   │   ├── student.py       # /api/me/* (events, register, attendance, notifications)
│   │   ├── admin.py         # /api/admin/* (events CRUD, attendance, notifications, users, reports)
│   │   └── notifications.py # /api/notifications
│   ├── services/
│   │   ├── __init__.py
│   │   ├── db.py            # DB layer (Firebase OR local JSON fallback)
│   │   └── notifier.py      # Email + push (stub) sender
│   ├── templates/
│   │   ├── public_dashboard.html
│   │   ├── auth.html
│   │   ├── student_dashboard.html
│   │   └── admin_dashboard.html
│   └── static/
│       ├── css/style.css
│       └── js/api.js
├── scripts/
│   └── seed_data.py         # Standalone seed runner
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Setup (in VS Code)

### Step 1 — Open the folder
Open the `wdc_app/` folder in VS Code.

### Step 2 — Create a virtual environment
Open the VS Code terminal (`Ctrl+\`` or `Cmd+\``):

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment
```bash
cp .env.example .env
```
Open `.env` in VS Code and review defaults. For a college demo, leave `USE_FIREBASE=false` — the app will use a local JSON file as the database.

### Step 5 — Run the app
```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
[WDC] Using LOCAL JSON backend (USE_FIREBASE=false).
[WDC] Empty DB detected — running seed...
[WDC] Seed complete.
```

### Step 6 — Open in browser
Go to: **http://127.0.0.1:8000**

The public WDC dashboard opens first. Click "Student Login" to sign in or sign up.

---

## 4. Switching to Real Firebase (later)

When you have a real Firebase project:

1. Go to Firebase Console → Project Settings → Service Accounts → Generate new private key.
2. Save the downloaded JSON as `serviceAccountKey.json` in the project root (`wdc_app/`).
3. Edit `.env`:
   ```
   USE_FIREBASE=true
   FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json
   ```
4. Restart uvicorn. The app will now use Firestore. All endpoints work identically.

> **Never commit `serviceAccountKey.json`** — it's in `.gitignore`.

---

## 5. API Endpoints

Full list (see `api_spec.json` for the original spec):

### Public
- `GET  /api/events` — list published events
- `GET  /api/events/{id}` — single event detail
- `GET  /api/women-dates` — women's observance days
- `GET  /api/speakers` — list speakers
- `GET  /api/health` — health check

### Auth
- `POST /api/auth/signup` — student sign up
- `POST /api/auth/login` — student login
- `POST /api/auth/logout` — logout
- `POST /api/auth/admin/login` — admin/staff login
- `GET  /api/auth/me` — current user (with permissions)

### Student (`/api/me`)
- `GET  /api/me` — profile
- `GET  /api/me/events` — my registrations
- `POST /api/me/events/{id}/register` — register
- `DELETE /api/me/events/{id}/register` — cancel
- `GET  /api/me/attendance` — my attendance
- `GET  /api/me/notifications` — my notifications
- `POST /api/me/notifications/{id}/read` — mark read

### Admin (`/api/admin`)
- `GET    /api/admin/events`
- `POST   /api/admin/events`
- `PATCH  /api/admin/events/{id}`
- `DELETE /api/admin/events/{id}`
- `GET    /api/admin/events/{id}/participants`
- `POST   /api/admin/attendance`
- `POST   /api/admin/attendance/import`
- `POST   /api/admin/notifications`
- `GET    /api/admin/users`
- `PATCH  /api/admin/users/{id}/role`
- `GET    /api/admin/reports`
- `GET    /api/admin/stats`
- `GET    /api/admin/speakers`
- `POST   /api/admin/speakers`
- `GET    /api/admin/women-dates`
- `POST   /api/admin/women-dates`

Interactive API docs: **http://127.0.0.1:8000/docs** (Swagger UI auto-generated by FastAPI).

---

## 6. Re-seeding the Database

If you want to wipe and re-seed the local DB:

```bash
# Stop the server (Ctrl+C)
# Delete the local DB file
rm local_db.json

# Restart — auto-seeds on startup
uvicorn app.main:app --reload
```

Or run the seed script directly:
```bash
python scripts/seed_data.py
```

---

## 7. Tech Notes

- **No certificate module, no gallery module** — per requirements. Attendance records participation instead.
- **Browser push + email notifications** are stubbed (print to console) when SMTP / VAPID keys are not configured. Wire them up in `.env` for production.
- **JWT tokens** are stored in both an HTTP-only cookie and `localStorage` so the frontend JS can read them. Token expiry: 12 hours.
- **Audit logs** — every privileged admin action (create/update/delete event, change role, send notification, mark attendance) is recorded in the `audit_logs` collection.
- **Responsive design** — purple/pink/lavender theme from `design_tokens.json`, works on desktop / tablet / mobile.

---

## 8. Troubleshooting

**Q: `ModuleNotFoundError: No module named 'fastapi'`**
A: Activate your venv first (`venv\Scripts\activate` on Windows / `source venv/bin/activate` on macOS/Linux).

**Q: Port 8000 already in use**
A: Run on a different port: `uvicorn app.main:app --reload --port 8001`

**Q: Want to reset everything**
A: Delete `local_db.json` and restart.

**Q: Firebase init failed**
A: Make sure `serviceAccountKey.json` exists at the path in `.env`. Or set `USE_FIREBASE=false` to use local mode.

---

## 9. License & Credits

Built for the Women Development Cell college project.
Spec source: `WDC_APP_FINAL_MASTER_PACKAGE.zip` (final pre-coding specification).
