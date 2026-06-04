# tests/auth/test_login.py

def test_successful_login_with_active_account(client, register_and_activate_user):
    """Test that a registered and activated user receives valid JWT access tokens."""
    # 1. One line registers and activates the user!
    _, payload, _ = register_and_activate_user()

    # 2. Attempt login
    login_payload = {
        "identifier": payload["username"],
        "password": payload["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data and data["token_type"] == "Bearer"


def test_login_fails_if_account_is_inactive(client, register_test_user):
    """Test that an unverified/inactive user is blocked from logging in."""
    # Register a user but DO NOT activate them
    _, payload = register_test_user()

    login_payload = {
        "identifier": payload["username"],
        "password": payload["password"]
    }
    response = client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 400, f"Failed to login: {response.json()}"


def test_login_fails_with_wrong_password(client, register_and_activate_user):
    """Test that providing an incorrect password returns an unauthorized error."""
    # 1. Create our active user quickly
    _, payload, _ = register_and_activate_user()

    # 2. Attempt login with a bad password
    login_payload = {
        "identifier": payload["username"],
        "password": "WrongPasswordX!"
    }
    response = client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 401, f"Failed to login: {response.json()}"
