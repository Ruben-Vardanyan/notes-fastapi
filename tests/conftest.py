# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import User
from main import app
from app.core.database import Base, get_db

SQLITE_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Builds and tears down database tables automatically before/after every test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides an isolated database session link."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Creates a base test client with database overrides and disabled rate-limiting."""

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db

    # Force SlowAPI to stay quiet during test sessions
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def register_test_user(client, raw_user_payload):
    """
    A helper utility fixture that handles hitting the registration endpoint.
    Returns a function so you can dynamically override values if needed.
    """

    def _register(custom_username=None, custom_email=None):
        payload = raw_user_payload.copy()
        if custom_username:
            payload["username"] = custom_username
        if custom_email:
            payload["email"] = custom_email

        response = client.post("/api/v1/auth/register", json=payload)
        return response, payload

    return _register


@pytest.fixture(scope="function")
def raw_user_payload():
    """
    Provides a standardized, valid dictionary payload for creating a user.
    Perfect for registration, login, and validation testing.
    """
    return {
        "username": "auth_test_user",
        "email": "auth_test@example.com",
        "password": "SecurePassword123!"
    }


@pytest.fixture(scope="function")
def register_test_user(client, raw_user_payload):
    """
    A helper utility fixture that handles hitting the registration endpoint.
    Returns a function so you can dynamically override values if needed.
    """

    def _register(custom_username=None, custom_email=None):
        payload = raw_user_payload.copy()
        if custom_username:
            payload["username"] = custom_username
        if custom_email:
            payload["email"] = custom_email

        response = client.post("/api/v1/auth/register", json=payload)

        return response, payload

    return _register


@pytest.fixture(scope="function")
def register_and_activate_user(register_test_user, db_session):
    """
    A helper fixture that registers a user AND immediately forces
    their account status to active inside the SQLite sandbox database.
    """

    def _create_active(custom_username=None, custom_email=None):
        # 1. Register using our existing factory
        response, payload = register_test_user(custom_username, custom_email)

        assert response.status_code == 201, f"Registration failed! Code: {response.status_code}, Body: {response.json()}"

        user_id = response.json()["user"]["id"]

        # 2. Force activate in the database sandbox
        user_record = db_session.query(User).filter(User.id == user_id).first()
        if user_record:
            user_record.is_active = True
            db_session.commit()
            db_session.refresh(user_record)

        # Return everything so your tests have all the data they need
        return response, payload, user_id

    return _create_active


@pytest.fixture(scope="function")
def authenticated_client(client, register_and_activate_user):
    """
    Creates a pre-authenticated test client.
    Automatically registers a user, activates them, logs them in,
    and attaches their JWT Bearer token to all outgoing requests.
    """
    # 1. Register and activate our user via our auth conftest factory
    _, payload, user_id = register_and_activate_user()

    # 2. Log in to get the access token
    login_payload = {
        "identifier": payload["username"],
        "password": payload["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    access_token = response.json()["access_token"]

    # 3. Inject the authorization token into the client headers permanently
    client.headers.update({"Authorization": f"Bearer {access_token}"})

    # 4. Yield the client and the user_id so tests know WHO owns the notes
    yield client, user_id

