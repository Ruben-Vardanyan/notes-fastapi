# Notes FastAPI

### Short description

Practicing FastAPI by creating a notes API

The application allows users to create notes with a title and content,
and share them with other users, assigning either viewer or editor roles.

Users can register within the app and verify their account 
via a confirmation link sent to their email address.

The authentication system is built using JWT. 
Refresh tokens are automatically blacklisted after every rotation, 
and active access tokens are instantly invalidated upon logout.

Users can also securely reset their passwords if forgotten by requesting 
a password-reset link sent directly to their email address.

### Features

- JWT Authentication
- User Registration & Login
- Email Validation
- Rate Limiting
- Redis Caching
- Scheduled Background Tasks
- PostgreSQL Database
- Database Migrations
- RESTful API Design
- Automated Testing

---

## Tech Stack
 
| Layer | Library |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL (psycopg2) |
| Migrations | Alembic |
| Auth | PyJWT / python-jose + Passlib (bcrypt) |
| Caching | Redis |
| Scheduling | APScheduler |
| Rate Limiting | SlowAPI |
| Testing | Pytest |
| Config | Python Dotenv |
 
---

## Setup
 
### 1. Clone & Install
 
```bash
git clone https://github.com/Ruben-Vardanyan/notes-fastapi.git
cd notes-fastapi
 
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
 
pip install -r requirements.txt
```
 
### 2. Environment Variables
 
Create a `.env` file in the project root:
 
```ini
PROJECT_NAME      = "Notes FastAPI"
API_BASE_URL      = "http://127.0.0.1:8000"
FRONTEND_BASE_URL = "http://127.0.0.1:3000"
DEBUG             = True
SECRET_KEY        = "your-super-secret-random-signing-key"
 
# Database
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_USER     = "your-postgres-user"
DB_PASSWORD = "your-postgres-password"
DB_NAME     = "your-database-name"
 
# SMTP (for verification & password reset emails)
EMAIL_FROM     = "your-system-email@example.com"
EMAIL_PASSWORD = "your-smtp-app-password"
```
 
### 3. Database Migrations
 
If migrations don't exist yet, initialise Alembic first:
 
```bash

alembic init migrations
```
 
Then update `migrations/env.py` to wire in your models and database URL:
 
```python
from app.core.config import settings
from app.models.base import Base
 
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
 
target_metadata = Base.metadata
```
 
Generate and apply migrations:
 
```bash

alembic revision --autogenerate -m "initial"
alembic upgrade head
```
 
### 4. Run
 
```bash

uvicorn main:app --reload
```
 
Interactive API docs available at **http://127.0.0.1:8000/docs**
