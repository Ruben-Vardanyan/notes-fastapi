# tests/auth/test_activation.py
import pytest

from app.models.verification_code import VerificationCode, VerificationType


@pytest.mark.skip
def test_user_activation_flow(client, register_test_user, db_session):
    # create user
    resp, payload = register_test_user()

    assert resp.status_code == 201

    data = resp.json()
    assert "id" in data["user"]
    assert "is_active" in data["user"] and data["user"]["is_active"] is False
    assert "access_token" in data
    user_id = data["user"]["id"]
    access_token = data["access_token"]

    # create and send verification code to user's email
    headers = {"Authorization": f"Bearer {access_token}"}
    req_token_resp = client.post("/api/v1/auth/request-verification", headers=headers)
    assert req_token_resp.status_code == 200, req_token_resp.json()

    # take verification code from db
    verification_record = db_session.query(VerificationCode).filter(
        VerificationCode.user_id == user_id,
        VerificationCode.purpose == VerificationType.EMAIL_VERIFICATION
    ).order_by(VerificationCode.created_at.desc()).first()

    assert verification_record is not None, "Verification record was not created in DB."
    activation_token = verification_record.token

    # verify email
    verify_email_resp = client.get(f"/api/v1/auth/verify-email/{activation_token}")
    assert verify_email_resp.status_code == 200, verify_email_resp.json()

    # try to login
    login_payload = {
        "identifier": payload["username"],
        "password": payload["password"]
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    data = login_resp.json()
    assert login_resp.status_code == 200, login_resp.json()
    assert "is_active" in data["user"] and data["user"]["is_active"] is True
