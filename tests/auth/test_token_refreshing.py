# tests/auth/test_refresh.py
from app.models.base import User


def test_successful_token_refresh_rotation(client, register_and_activate_user):
    """Happy Path: Submitting a valid refresh token yields fresh access/refresh pairs."""
    # 1. Setup active user session
    _, payload, _ = register_and_activate_user()
    login_resp = client.post("/api/v1/auth/login",
                             json={"identifier": payload["username"], "password": payload["password"]})
    old_tokens = login_resp.json()

    # 2. Hit the refresh endpoint with the valid refresh token
    refresh_payload = {"refresh_token": old_tokens["refresh_token"]}
    refresh_resp = client.post("/api/v1/auth/refresh", json=refresh_payload)

    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    # Security check: The new refresh token MUST be a newly generated string
    assert new_tokens["refresh_token"] != old_tokens["refresh_token"]


def test_refresh_fails_with_access_token_type(client, register_and_activate_user):
    """Sad Path: Submitting a valid token but of type 'access' must be explicitly rejected."""
    _, payload, _ = register_and_activate_user()
    login_resp = client.post("/api/v1/auth/login",
                             json={"identifier": payload["username"], "password": payload["password"]})
    tokens = login_resp.json()

    # Send the ACCESS token to the REFRESH endpoint deliberately
    bad_payload = {"refresh_token": tokens["access_token"]}
    response = client.post("/api/v1/auth/refresh", json=bad_payload)

    assert response.status_code == 401
    assert "refresh token is required" in response.json()["detail"].lower()


def test_refresh_token_reuse_triggers_breach_detection(client, register_and_activate_user, db_session):
    """
    Breach Path: Reusing an already spent refresh token indicates a theft/replay exploit.
    The backend should block execution and invalidate all of the user's active sessions.
    """
    # 1. Setup active user session
    _, payload, user_id = register_and_activate_user()
    login_resp = client.post("/api/v1/auth/login",
                             json={"identifier": payload["username"], "password": payload["password"]})
    tokens = login_resp.json()

    original_refresh_token = tokens["refresh_token"]

    # 2. ROTATION 1 (Legitimate Use): Use the token once. This moves it into the blacklist table.
    first_refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh_token})
    assert first_refresh_resp.status_code == 200

    # 3. ROTATION 2 (The Attack): Try to reuse the exact same token a second time
    malicious_refresh_resp = client.post("/api/v1/auth/refresh", json={"refresh_token": original_refresh_token})

    # Assert that the security system successfully caught the attack
    assert malicious_refresh_resp.status_code == 401
    assert "security alert" in malicious_refresh_resp.json()["detail"].lower()

    # 4. VERIFY PUNISHMENT: Query the live DB sandbox to confirm logged_out_at was force stamped
    db_session.expire_all()  # Clear cache to force a real database read
    compromised_user = db_session.query(User).filter(User.id == user_id).first()

    assert compromised_user.logged_out_at is not None


# tests/auth/test_refresh.py

def test_refresh_token_handles_inactive_user_correctly(client, register_test_user, db_session):
    """
    Test how the refresh endpoint handles a user who is registered but INACTIVE.
    Since get_current_inactive_user allows inactive profiles, this should either
    rotate successfully or fail gracefully based on your business logic.
    """
    # 1. Register a user but DO NOT activate them (is_active stays False)
    resp, payload = register_test_user()
    assert resp.status_code == 201
    tokens = resp.json()

    # 2. Attempt to rotate using the inactive user's refresh token
    refresh_payload = {"refresh_token": tokens["refresh_token"]}
    refresh_resp = client.post("/api/v1/auth/refresh", json=refresh_payload)

    # ─── EXPECTED BEHAVIOR ───
    # If your business rules allow unverified accounts to refresh sessions:
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens

    # NOTE: If your token_service.refresh_access_token explicitly checks
    # and blocks inactive users downstream, change the assertion above to:
    # assert refresh_resp.status_code == 400
    # assert "inactive" in refresh_resp.json()["detail"].lower()