# tests/auth/test_forgot_password.py
from datetime import datetime, timezone, timedelta

import pytest

from app.models.verification_code import VerificationCode, VerificationType
from app.models.user import User


@pytest.mark.skip
def test_forgot_and_reset_password_success_lifecycle(client, register_and_activate_user, db_session):
    """Happy Path: Complete password recovery workflow from email link generation to global session revocation."""
    # 1. Register an active user
    _, payload, user_id = register_and_activate_user()

    # 2. Trigger Forgot Password request
    forgot_resp = client.post("/api/v1/auth/forgot-password", json={"email": payload["email"]})
    assert forgot_resp.status_code == 200
    assert "dispatched" in forgot_resp.json()["detail"].lower()

    # 3. Intercept and grab the token from the SQLite sandbox database
    db_session.expire_all()
    verification_record = db_session.query(VerificationCode).filter(
        VerificationCode.user_id == user_id,
        VerificationCode.purpose == VerificationType.PASSWORD_RESET
    ).first()

    assert verification_record is not None
    assert verification_record.used_at is None

    # 4. Consume token to perform a password reset
    reset_payload = {
        "token": verification_record.token,
        "new_password": "CompletelyNewPassword999!"
    }
    reset_resp = client.post("/api/v1/auth/reset-password", json=reset_payload)
    assert reset_resp.status_code == 200
    assert "successfully updated" in reset_resp.json()["detail"].lower()

    # 5. VERIFY SECURITY: Check that old password fails to log in, but new password works
    bad_login_resp = client.post("/api/v1/auth/login",
                                 json={"identifier": payload["username"], "password": payload["password"]})
    assert bad_login_resp.status_code == 401, bad_login_resp.json()  # Old password dead!

    good_login_resp = client.post("/api/v1/auth/login",
                                  json={"identifier": payload["username"], "password": "CompletelyNewPassword999!"})
    assert good_login_resp.status_code == 200  # New password works!

    # 6. VERIFY GLOBAL REBORN STATUS: Ensure user's logged_out_at timestamp was set to enforce global device revoking
    db_session.refresh(verification_record)
    user_record = db_session.query(User).filter(User.id == user_id).first()
    assert verification_record.used_at is not None
    assert user_record.logged_out_at is not None


@pytest.mark.skip
def test_forgot_password_account_enumeration_protection(client):
    """Security Path: Submitting a non-existent email must return 200 OK identical details."""
    fake_payload = {"email": "i_do_not_exist_anywhere@example.com"}
    response = client.post("/api/v1/auth/forgot-password", json=fake_payload)

    assert response.status_code == 200
    # The message should match exactly what valid users see
    assert "dispatched" in response.json()["detail"].lower()


@pytest.mark.skip
def test_reset_password_fails_if_token_reused(client, register_and_activate_user, db_session):
    """Sad Path: Reusing an already spent verification code must be rejected immediately."""
    _, payload, user_id = register_and_activate_user()
    client.post("/api/v1/auth/forgot-password", json={"email": payload["email"]})

    verification_record = db_session.query(VerificationCode).filter(
        VerificationCode.user_id == user_id,
        VerificationCode.purpose == VerificationType.PASSWORD_RESET
    ).first()

    reset_payload = {
        "token": verification_record.token,
        "new_password": "ValidPassword1!"
    }

    # First attempt: succeeds
    resp1 = client.post("/api/v1/auth/reset-password", json=reset_payload)
    assert resp1.status_code == 200

    # Second attempt: fails because verification_record.used_at is already set
    resp2 = client.post("/api/v1/auth/reset-password", json=reset_payload)
    assert resp2.status_code == 400
    assert "already been used" in resp2.json()["detail"].lower()


@pytest.mark.skip
def test_reset_password_fails_if_token_expired(client, register_and_activate_user, db_session):
    """Sad Path: Submitting an expired token must result in validation refusal."""
    _, payload, user_id = register_and_activate_user()
    client.post("/api/v1/auth/forgot-password", json={"email": payload["email"]})

    verification_record = db_session.query(VerificationCode).filter(
        VerificationCode.user_id == user_id,
        VerificationCode.purpose == VerificationType.PASSWORD_RESET
    ).first()

    # Force mock the token's lifetime expiration to 1 hour ago in the database sandbox
    verification_record.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    reset_payload = {
        "token": verification_record.token,
        "new_password": "ExpiredTokenPassword1!"
    }
    response = client.post("/api/v1/auth/reset-password", json=reset_payload)

    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()
