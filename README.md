# Authentication Service

A production-grade authentication service built with **FastAPI**, **PostgreSQL**, and **JWT**. Exposes endpoints for user registration, login, and infrastructure health checks following a strict four-layer architecture.

---

## Overview

| Feature | Technology |
|---|---|
| Web framework | FastAPI 0.115 |
| Database | PostgreSQL 15+ (async via `asyncpg`) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic 1.16 |
| Password hashing | passlib[bcrypt] (work factor ≥ 12) |
| Token issuance | python-jose HS256 JWT |
| Config management | pydantic-settings (`.env` file) |
| Testing | pytest + hypothesis (property-based) |

---

## Prerequisites

- Python 3.11 or newer
- PostgreSQL 15+ running and accessible
- `pip` (comes with Python)

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd user-auth-module
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
# Runtime + dev/test dependencies
pip install -e ".[dev]"
```

### 4. Copy and configure the environment file

```bash
cp .env.example .env
```

Edit `.env` and fill in your real values (see [Environment Variables](#environment-variables) below).

---

## Environment Variables

All configuration is loaded from `.env` at startup via `pydantic-settings`. Copy `.env.example` to `.env` and set each value.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Async PostgreSQL DSN: `postgresql+asyncpg://user:password@host:port/db` |
| `JWT_SECRET_KEY` | ✅ | — | Secret used to sign and verify JWT tokens. Use a long random string in production. |
| `BCRYPT_WORK_FACTOR` | — | `12` | bcrypt cost factor. Increase for higher security (slower). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `30` | Access token lifetime in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | — | `7` | Refresh token lifetime in days. |
| `APP_NAME` | — | `Authentication Service` | Application name returned by the root endpoint. |
| `APP_VERSION` | — | `1.0.0` | Application version returned by the root endpoint. |
| `DEBUG` | — | `False` | Enable debug mode. **Never set to `True` in production.** |

---

## Running the Server

```bash
# Development — auto-reload on file changes
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`.  
Interactive Swagger docs: `http://localhost:8000/docs`  
ReDoc docs: `http://localhost:8000/redoc`

---

## Database Setup

The application connects to an existing PostgreSQL database. Ensure the `users` table exists with the schema matching `src/models/user.py` before starting the server. The required table structure:

```sql
CREATE TABLE users (
    id               SERIAL PRIMARY KEY,
    user_name        VARCHAR(50)  NOT NULL,
    user_email       VARCHAR(254) NOT NULL,
    phone_no         VARCHAR(10)  NOT NULL,
    hashed_password  TEXT         NOT NULL,
    refresh_token    TEXT,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uix_users_email ON users (LOWER(user_email));
CREATE UNIQUE INDEX uix_users_phone ON users (phone_no);
```

---

## Running Tests

```bash
# Run the full test suite
pytest tests/ -v

# Run only unit tests (fast, no DB required)
pytest tests/utils/ tests/services/ -v

# Run only integration tests
pytest tests/repositories/ tests/routes/ tests/database/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Run property-based tests with more examples (CI mode)
HYPOTHESIS_PROFILE=ci pytest tests/ -v
```

> **Note:** Integration tests require a running PostgreSQL instance configured in `.env`.

---

## Project Structure

```
user-auth-module/
├── main.py                         # FastAPI app entry point — routers + exception handlers
├── pyproject.toml                  # Project metadata and pinned dependencies
├── .env.example                    # Template for environment variables (no secrets)
├── .env                            # Local environment variables (git-ignored)
├── .gitignore
├── README.md
│
├── alembic.ini                     # Alembic configuration
├── alembic/
│   ├── env.py                      # Alembic env — reads DATABASE_URL from settings
│   └── versions/
│       └── <timestamp>_initial.py  # Initial migration (users table)
│
├── src/
│   ├── __init__.py
│   ├── settings.py                 # pydantic-settings — loads from .env
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # SQLAlchemy ORM model (users table)
│   │   └── schemas.py              # Pydantic request/response schemas
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── connection.py           # Async engine, session factory, get_db_session()
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user_repository.py      # Data access — CRUD operations on users table
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── auth_service.py         # Business logic — register, login
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # POST /api/v1/register, POST /api/v1/login
│   │   └── default.py              # GET /, GET /health, GET /ready
│   │
│   └── utils/
│       ├── __init__.py
│       ├── constants.py            # All UPPER_SNAKE_CASE constants and message strings
│       ├── exceptions.py           # AppException hierarchy
│       ├── logger.py               # Configured auth_service logger
│       ├── password.py             # PasswordHasher (bcrypt)
│       └── jwt_handler.py          # JWTHandler (HS256 access + refresh tokens)
│
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Shared fixtures: async_client, db_session, hypothesis profiles
    │
    ├── utils/
    │   ├── __init__.py
    │   ├── test_constants.py
    │   ├── test_password.py        # P6: hash round-trip property test
    │   └── test_jwt_handler.py     # P15, P16, P18: JWT property tests
    │
    ├── models/
    │   ├── __init__.py
    │   └── test_schemas.py         # P1–P5, P11: schema validation property tests
    │
    ├── database/
    │   ├── __init__.py
    │   └── test_connection.py
    │
    ├── repositories/
    │   ├── __init__.py
    │   └── test_user_repository.py # P7 + integration tests
    │
    ├── services/
    │   ├── __init__.py
    │   └── test_auth_service.py    # Unit tests with mocked dependencies
    │
    └── routes/
        ├── __init__.py
        ├── test_auth.py            # P8–P10, P12–P14, P17, P19–P20 + integration tests
        └── test_default.py         # Unit tests for /, /health, /ready
```

---

## API Endpoints

### Health & Info

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/` | Returns app name and version | None |
| `GET` | `/health` | Liveness check — confirms process is running | None |
| `GET` | `/ready` | Readiness check — probes database (5 s timeout) | None |

**`GET /` response:**
```json
{
  "name": "Authentication Service",
  "version": "1.0.0"
}
```

**`GET /health` response:**
```json
{ "status": "ok" }
```

**`GET /ready` response (success):**
```json
{ "status": "ready" }
```

**`GET /ready` response (failure):**
```
HTTP 503 Service Unavailable
```

---

### Authentication

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/register` | Register a new user | None |
| `POST` | `/api/v1/login` | Login and receive JWT tokens | None |

---

#### `POST /api/v1/register`

**Request body:**
```json
{
  "user_name": "jane_doe",
  "user_email": "jane@example.com",
  "phone_no": "9876543210",
  "password": "MyP@ssw0rd"
}
```

| Field | Type | Rules |
|---|---|---|
| `user_name` | string | 3–50 characters |
| `user_email` | string | Valid RFC 5322 email, max 254 characters |
| `phone_no` | string | Exactly 10 digits (`^[0-9]{10}$`) |
| `password` | string | Min 8 chars; must contain uppercase, lowercase, digit, and special character |

**Success response (HTTP 200):**
```json
{
  "status_code": 200,
  "message": "User profile created successfully"
}
```

**Error responses:**

| HTTP Status | Condition |
|---|---|
| `400` | Missing required field |
| `409` | Email already registered |
| `409` | Phone number already registered |
| `422` | Validation failure (format, length, password strength) |
| `500` | Internal server error |

---

#### `POST /api/v1/login`

**Request body:**
```json
{
  "user_email": "jane@example.com",
  "password": "MyP@ssw0rd"
}
```

| Field | Type | Rules |
|---|---|---|
| `user_email` | string | Valid RFC 5322 email, max 254 characters |
| `password` | string | Max 128 characters |

**Success response (HTTP 200):**
```json
{
  "access_token": "<jwt-token>",
  "token_type": "Bearer",
  "message": "Login successfully"
}
```

**Error responses:**

| HTTP Status | Condition |
|---|---|
| `400` | Missing required field |
| `401` | Invalid credentials (wrong password) |
| `404` | User not found |
| `422` | Validation failure |
| `500` | Internal server error |

---

## License

MIT
