# tests/auth/test_logout.py

def test_user_logout(client, register_and_activate_user):
    # 1. Safely create your active user database state
    _, payload, _ = register_and_activate_user()

    # 2. Log in to get your active token session
    login_payload = {
        "identifier": payload["username"],
        "password": payload["password"]
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200

    data = login_resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    logout_payload = {
        "refresh_token": data["refresh_token"],
    }

    # 3. Now test your logout/blacklisting endpoint!
    logout_resp = client.post("/api/v1/auth/logout", headers=headers, json=logout_payload)
    assert logout_resp.status_code == 200  # Or 204 depending on your route design

    # The second attempt must fail because the session was just invalidated!
    logout_resp = client.post("/api/v1/auth/logout", headers=headers, json=logout_payload)
    assert logout_resp.status_code == 401
