# CTF Platform

An educational Capture The Flag platform designed for ASIR (Network Systems Administration) students, specifically for the **Seguridad y Alta Disponibilidad** module. Built as a TFM (Master's Final Project) for the Master's in Secondary Education Teacher Training.

## Overview

The platform provides a gamified learning environment where students solve security challenges based on the OWASP Top 10. Each challenge runs in an isolated Docker container with a unique flag per student, preventing answer sharing. Teachers manage the session through a dedicated admin panel.

## Architecture
ctf-platform/
├── backend/        # FastAPI (Python) — REST API
├── frontend/       # React + Vite + TypeScript — SPA
├── challenges/     # Modular challenge definitions (YAML + Dockerfile)
└── infra/          # Nginx, Ansible, Docker Compose

### Tech stack

| Layer | Technology | Reason |
|---|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 | Async, typed, auto-docs |
| Database | PostgreSQL 16 | Relational integrity, materialized views |
| Cache / Rate limiting | Redis 7 | Atomic counters, TTL-based expiry |
| Frontend | React 18 + Vite + TypeScript | Fast DX, type safety |
| State management | Zustand + React Query | Minimal boilerplate, server cache |
| Styling | Tailwind CSS | Utility-first, consistent dark theme |
| Container orchestration | Docker SDK for Python | Direct API access, per-user isolation |
| Auth | JWT (HS256) + bcrypt | Stateless, secure password hashing |
| CI/CD | GitHub Actions | Automated test and deploy pipeline |
| Provisioning | Ansible | Reproducible server setup |

## Features

### Student features
- Login with credentials provided by teacher
- Browse available challenges ordered by difficulty
- Launch private Docker instances of vulnerable applications
- Submit flags with immediate feedback
- Use hints (with configurable point deduction)
- View personal progress and class scoreboard

### Teacher features
- Admin panel with real-time class overview
- Activate/deactivate challenges per session
- Monitor running containers across all students
- Emergency stop — kill all containers instantly
- Import student list from Excel (.xlsx)
- Export results to Excel for gradebook
- Disable individual student accounts

### Security design
- **Per-user flags** — flags generated with HMAC-SHA256 keyed on `user_id + challenge_slug`. Students cannot share flags.
- **Hint timing** — hint point deductions only apply if the hint was used before solving. Revealing a hint after solving has no effect.
- **Rate limiting** — flag submission is limited to 10 attempts per challenge per 60 seconds via Redis atomic counters.
- **Constant-time comparison** — flag validation uses `hmac.compare_digest` to prevent timing attacks.
- **Network isolation** — each student's containers run on a dedicated Docker bridge network, preventing cross-student access.
- **Least privilege** — container volumes mounted read-only where possible. Resource limits (CPU, RAM) enforced per container.

## Challenge system

Challenges are self-contained directories under `challenges/`. Adding a new challenge requires no code changes — the backend discovers and registers challenges automatically on startup.

### Challenge structure
challenges/
└── web-sqli-01/
├── challenge.yml    # Metadata and configuration
├── Dockerfile       # Vulnerable application image
├── app/             # Application source code
├── solve.py         # Official solution (teacher reference)
└── writeup.md       # Explanation for post-challenge review

### challenge.yml contract

```yaml
id: web-sqli-01
name: "Login with SQL Injection"
type: docker          # docker | file
category: web
owasp: A03
difficulty: easy
points: 100
required: true

description: |
  A login form is protecting the admin panel.
  Can you get in without knowing the password?

flag_type: dynamic    # dynamic (HMAC per user) | static (same for all)

docker:
  image: ctf/web-sqli-01
  port: 5000
  ttl: 7200
  cpu: "0.5"
  memory: "128m"

hints:
  - cost: 0
    text: "Try entering a single quote in the username field."
  - cost: 50
    text: "The query looks like: SELECT * FROM users WHERE username='INPUT'"
```

### Available challenges

| # | Name | OWASP | Difficulty | Type | Required |
|---|---|---|---|---|---|
| 1 | Login with SQL Injection | A03 | Easy | Docker | Yes |
| 2 | XSS — Steal the cookie | A03 | Easy | Docker | Yes |
| 3 | IDOR — Access another user's record | A01 | Easy | Docker | Yes |
| 4 | JWT — Escalate to admin | A07 | Medium | Docker | Yes |
| 5 | Path Traversal — Read /flag.txt | A05 | Medium | Docker | Yes |
| 6 | SSRF — Access internal service | A10 | Medium | Docker | Yes |
| 7 | Traffic analysis — Find credentials | A02 | Medium | File | No |
| 8 | Mass Assignment — Escalate via API | A01 | Hard | Docker | No |

## Getting started

### Prerequisites

- Docker 24+
- Docker Compose v2
- Python 3.11+
- Node 18+
- uv (`pipx install uv`)

### Local development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ctf-platform.git
cd ctf-platform

# Copy environment config
cp .env.example .env
# Edit .env — set DATABASE_URL and REDIS_URL to localhost for local dev

# Start infrastructure
docker compose up db redis -d

# Backend
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -r pyproject.toml
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Build challenge images

```bash
docker build -t ctf/web-sqli-01 challenges/web-sqli-01/
```

### Create initial users

```bash
# Register a teacher
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher","email":"teacher@example.com","password":"yourpassword","full_name":"Teacher Name","role":"teacher"}'

# Import students from Excel via admin panel at /admin
```

### Environment variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://ctf:pass@localhost:5432/ctfdb` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing secret | Long random string |
| `FLAG_HMAC_SECRET` | Flag generation secret (keep separate from SECRET_KEY) | Long random string |
| `FLAG_PREFIX` | Flag format prefix | `CTF` |
| `ENVIRONMENT` | `development` or `production` | `development` |
| `ALLOWED_ORIGINS` | CORS allowed origins (JSON array) | `["http://localhost:5173"]` |

## API documentation

Interactive API docs available at `http://localhost:8000/api/docs` when running in development mode.

### Key endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/login` | — | Login, returns JWT |
| POST | `/api/auth/register` | — | Register new user |
| GET | `/api/auth/me` | User | Current user profile |
| GET | `/api/challenges` | User | List active challenges |
| POST | `/api/challenges/{slug}/start` | User | Launch challenge container |
| POST | `/api/challenges/{slug}/submit` | User | Submit flag |
| GET | `/api/scoreboard` | User | Class scoreboard |
| POST | `/api/hints/{slug}/{index}` | User | Reveal hint |
| GET | `/api/admin/students` | Teacher | Student progress |
| POST | `/api/admin/import/students` | Teacher | Bulk import from Excel |
| GET | `/api/admin/export/results` | Teacher | Export results as Excel |
| DELETE | `/api/admin/containers/all` | Teacher | Emergency stop all containers |

## License

MIT
