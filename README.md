A structured, digital In-House Goal Setting & Tracking Portal built with Flask.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# 1. Clone and navigate
cd atomberg

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your SECRET_KEY

# 5. Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# 6. Seed demo data
python seed.py

# 7. Run the server
flask run
```

Visit: **http://localhost:5000**

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin / HR | admin@atomberg.com | admin123 |
| Manager (Engineering) | manager.eng@atomberg.com | manager123 |
| Manager (Marketing) | manager.mkt@atomberg.com | manager123 |
| Manager (Operations) | manager.ops@atomberg.com | manager123 |
| Employee | emp1@atomberg.com | emp123 |
| Employee | emp2@atomberg.com | emp123 |
| Employee | emp3@atomberg.com | emp123 |

## 📋 Features

### Phase 1 — Goal Creation & Approval
- Employee goal sheet drafting (Thrust Area, Title, UoM, Weightage)
- Validation: 100% total weightage, min 10% per goal, max 8 goals
- L1 Manager approval with inline editing
- Goal locking post-approval (Admin unlock required)
- Shared Goals — departmental KPIs pushed to multiple employees

### Phase 2 — Achievement Tracking & Quarterly Check-ins
- Log Actual vs. Planned achievements per quarter
- Status tracking: Not Started / On Track / Completed
- Manager check-in module with structured comments
- Auto-computed progress scores (Numeric, %, Timeline, Zero-based)

### Check-in Schedule
| Window | Period |
|--------|--------|
| Goal Setting | May |
| Q1 Check-in | July |
| Q2 Check-in | October |
| Q3 Check-in | January |
| Q4 / Annual | March-April |

### Reporting & Governance
- Achievement Report (CSV/Excel export)
- Completion Dashboard (real-time)
- Audit Trail (all post-lock changes)

### Bonus Features
- Microsoft Entra ID (Azure AD) SSO boilerplate
- Rule-based Escalation Module
- Analytics: QoQ trends, heatmaps, distribution charts, manager effectiveness

## 🏗️ Architecture

```text
Flask (Application Factory) + SQLAlchemy ORM + SQLite
├── Models:  User, Department, Goal, GoalSheet, SharedGoal,
│            Achievement, CheckInComment, PerformanceCycle,
│            AuditLog, Escalation
├── Routes:  auth, employee, manager, admin, reports, api
├── Services: goal, scoring, checkin, escalation, export, sso
└── Frontend: Jinja2 Templates + Vanilla CSS + Chart.js
```

## 🚀 Deployment

For production deployments, do not use `flask run` as it spins up a development server. Instead, use a production WSGI server. 

### Option 1: Local / Virtual Private Server (VPS) Deployment

**1. Install a WSGI server:**
*   **Windows:** Use `waitress`
    ```bash
    pip install waitress
    waitress-serve --port=5000 run:app
    ```
*   **Linux/macOS:** Use `gunicorn`
    ```bash
    pip install gunicorn
    gunicorn -w 4 -b 0.0.0.0:5000 run:app
    ```

**2. Set up a Reverse Proxy (Optional but Recommended):**
Use Nginx or Apache to proxy requests to port 5000, manage SSL certificates (via Let's Encrypt), and serve static files directly.

### Option 2: Cloud PaaS (Render / Heroku)

Since the project currently uses SQLite, deploying to an ephemeral file system (like Render or Heroku) will cause the database to reset on every new deployment or dyno restart.

**To deploy to Render/Heroku with persistent data:**
1. Provision a managed PostgreSQL or MySQL database addon.
2. Update the `.env` file's `DATABASE_URL` to point to the new remote database.
    ```env
    DATABASE_URL=postgresql://user:password@hostname:5432/dbname
    ```
3. Add a `Procfile` at the root of the repository:
    ```text
    web: gunicorn run:app
    ```
4. Push to your Git provider and link the repository to the PaaS platform.

## 📄 License

Built for ATOMQUEST HACKATHON 1.0
