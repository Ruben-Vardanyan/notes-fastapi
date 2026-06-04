import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.models.user import User
from main import app

SQLITE_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Automatically builds and tears down database tables before and after every test."""
    # Create all tables defined in your SQLAlchemy models mapping
    Base.metadata.create_all(bind=engine)
    yield
    # Safely drop all tables when a test is completed so the next test has a clean slate
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session link for test configurations."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Creates a test client that automatically overrides the production database dependency."""

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False

    # Swap the production dependency with our mock testing database session
    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear out overrides after the test finishes so production environments are untainted
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def authenticated_client(client, db_session):
    """
    Creates a pre-authenticated client by registering a user,
    manually activating them in the database sandbox, and logging them in.
    """
    # 1. Register the testing account structure
    username = "note_owner"
    email = "owner@example.com"
    password = "SecurePassword123!"

    client.post("/api/v1/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })

    # 2. Bypass email wait: Force activate the user directly in the test database
    user_record = db_session.query(User).filter(User.email == email).first()
    if user_record:
        user_record.is_active = True
        db_session.commit()  # Save the activated state to our SQLite sandbox

    # 3. Log them in now that they are active!
    login_response = client.post("/api/v1/auth/login", json={
        "identifier": username,
        "password": password
    })

    # Ensure login succeeded before grabbing token to catch setup bugs early
    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
    token = login_response.json()["access_token"]

    # 4. Inject the Authorization Header permanently for this test run
    client.headers.update({"Authorization": f"Bearer {token}"})

    yield client
