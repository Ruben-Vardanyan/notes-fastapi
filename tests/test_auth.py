# tests/test_auth.py
from app.models.user import User
from app.models.verification_code import VerificationCode, VerificationType


def test_register_user_success(client):
    """Test that a user can register successfully with valid data."""

    # 1. Arrange: Prepare the fake payload
    payload = {
        "username": "testuser1234567",
        "email": "testuser268@example.com",
        "password": "SecurePassword123!",
    }
    # 2. Act: Send a POST request to your auth endpoint
    response = client.post("/api/v1/auth/register", json=payload)

    data = response.json()
    assert "access_token" in data
    assert "user" in data

    # Check properties inside the returned user object safely
    assert data["user"]["username"] == payload["username"]
    assert data["user"]["email"] == payload["email"]
    assert "id" in data["user"]

#
# def test_user_email_activation_flow(client, db_session):
#     """
#     Tests the complete user registration lifecycle:
#     Registration (Inactive) -> Token Request -> Token Extraction -> Verification -> Activation.
#     """
#     email = "verify_me@example.com"
#     payload = {
#         "username": "activation_user",
#         "email": email,
#         "password": "SecurePassword123!"
#     }
#
#     # 1. Register the account
#     reg_response = client.post("/api/v1/auth/register", json=payload)
#     assert reg_response.status_code == 201
#
#     # 2. Verify they are initialized as INACTIVE in the database sandbox
#     user_record = db_session.query(User).filter(User.email == email).first()
#     assert user_record is not None
#     assert user_record.is_active is False
#
#     # 3. ─── NEW STEP: Explicitly request the verification token ───
#     headers = {"Authorization": f"Bearer {reg_response.json()['access_token']}"}
#     req_token_response = client.post("/api/v1/auth/request-verification", headers=headers)
#     assert req_token_response.status_code == 200  # or 202 depending on your background tasks setup
#
#     # 4. Extract the newly generated verification token from the database
#     verification_record = db_session.query(VerificationCode).filter(
#         VerificationCode.user_id == user_record.id,
#         VerificationCode.purpose == VerificationType.EMAIL_VERIFICATION
#     ).order_by(VerificationCode.created_at.desc()).first()
#
#     assert verification_record is not None, "Verification record was not created in DB."
#     activation_token = verification_record.token
#
#     # 5. Hit your verification endpoint route using the dynamic token path
#     activation_url = f"/api/v1/auth/verify-email/{activation_token}"
#     activation_response = client.get(activation_url)
#
#     # Asserting your custom 303 Redirect behavior!
#     assert activation_response.status_code == 200
#
#     # 6. Refresh the data instance context and assert status update
#     db_session.refresh(user_record)
#     assert user_record.is_active is True
