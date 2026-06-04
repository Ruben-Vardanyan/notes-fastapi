# Notes FastAPI

A secure, high-performance Notes Management API backend
built with **FastAPI**, **SQLAlchemy ORM**, and **PostgreSQL**.
This project features production-grade security defaults, including role-based
collaboration, rate limiting, and a multi-step secure email activation lifecycle.

---

## 🛠️ Tech Stack & Core Libraries

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) - High-performance, asynchronous web framework for building
  APIs.
* **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/) - Object-Relational Mapper for safe and pythonic database
  interactions.
* **Database Driver:** `psycopg2` - PostgreSQL adapter for Python.
* **Data Validation:** [Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/) - Validates request bodies
  and structures API JSON responses.
* **Security:** `PyJWT` - Implements secure JSON Web Tokens with access/refresh lifecycles and token blacklisting.
* **Rate Limiting:** `SlowAPI` - Protects endpoints against brute-force attacks and spam requests.

---

## 🔐 Security & User Lifecycle Workflow

This application implements a strict security pipeline to prevent fake account creation and unauthorized data access.

### 1. User Registration & Activation Flow

To verify user identities without third-party authentication overhead, accounts follow this sequential state logic:

1. **Register (`POST /auth/register`):** User creates an account. The database initializes them as **inactive** (
   `is_active = False`).
2. **Request Verification (`POST /auth/request-verification`):** Generates a cryptographically secure token using
   Python's `secrets.token_urlsafe(32)`.
3. **Email Handshake:** An automated transactional email is dispatched containing a unique, secure link embedded with
   the token.
4. **Activation (`GET /auth/verify-email/{token}`):** When the link is visited, the backend validates the token, flags
   the user account as **active** (`is_active = True`), and executes a clean HTTP `303 See Other` redirect to the
   frontend login dashboard.

### 2. Session Management

* **Dual Token Lifecycle:** Employs brief short-lived `access_tokens` for regular api requests and longer-lived
  `refresh_tokens` to seamlessly renew sessions.
* **Token Blacklisting:** Logging out or shifting permissions instantly flags tokens in a memory store to neutralize
  token-hijacking vulnerabilities.
* **Endpoint Rate-Limiting:** Essential routes (like `/register` and `/login`) are guarded by `SlowAPI` counters to drop
  automated credential-stuffing traffic.

---

## 🚀 Quick Start Setup Guide

### 1. Installation

Clone the repository and install the project dependencies inside a clean virtual environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/notes-fastapi.git
cd notes-fastapi

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt

```

### 2. Environment Configuration

Create a `.env` file in the project's root directory. The application reads these values safely at startup using
`pydantic-settings`:

```ini
PROJECT_NAME = "Notes FastAPI"
API_BASE_URL = "http://127.0.0.1:8000"
FRONTEND_BASE_URL = "http://127.0.0.1:3000"
DEBUG = True
SECRET_KEY = "your-super-secret-random-signing-key"

# Database Configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "your-secure-postgres-password"
DB_NAME = "notes_db"

# SMTP Email Configuration (For verification links)
EMAIL_FROM = "your-system-email@example.com"
EMAIL_PASSWORD = "your-smtp-app-password"

```

### 3. Running the Server

Launch the development server using `uvicorn`:

```bash
uvicorn main:app --reload

```

Once started, you can access the interactive API Swagger documentation hub directly at: **`http://127.0.0.1:8000/docs`**

