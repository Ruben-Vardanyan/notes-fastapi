def test_successful_registration(register_test_user):
    """Tests that a user can register cleanly with valid data."""
    # Run our conftest utility
    response, payload = register_test_user()

    assert response.status_code == 201
    assert response.json()["user"]["username"] == payload["username"]
    assert response.json()["user"]["email"] == payload["email"]
    assert response.json()["user"]["is_active"] == False


def test_cannot_register_duplicate_username_or_email(register_test_user):
    """Tests that the system blocks registering an existing username."""
    # Register the first user
    register_test_user(custom_username="duplicate_me", custom_email="first@example.com")

    # Try to register a second user with the same username but different email
    bad_response, _ = register_test_user(custom_username="duplicate_me", custom_email="second@example.com")

    assert bad_response.status_code == 400

    # Try to register a second user with the same username but different email
    bad_response, _ = register_test_user(custom_username="new", custom_email="first@example.com")

