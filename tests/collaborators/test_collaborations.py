# tests/notes/test_collaborations.py

def test_note_sharing_and_collaborator_permissions_lifecycle(
        client,
        authenticated_client,
        register_and_activate_user
):
    """
    Lifecycle Path: Tests sharing a note with another user, verifying
    collaborator read access, and blocking unauthorized collaborator actions.
    """
    # 1. SETUP USER A (The Owner)
    # auth_client_A has its headers set automatically by the fixture,
    # but since we are mutating the global client later, let's capture User A's token details explicitly if needed,
    # or just make sure we don't clobber headers globally.
    auth_client_A, user_A_id = authenticated_client

    # 2. SETUP USER B (The Collaborator)
    _, payload_B, user_B_id = register_and_activate_user(
        custom_username="collab_bob",
        custom_email="bob@example.com"
    )
    login_B = client.post("/api/v1/auth/login",
                          json={"identifier": payload_B["username"], "password": payload_B["password"]})
    token_B = login_B.json()["access_token"]
    headers_B = {"Authorization": f"Bearer {token_B}"}  # ◄─── KEEP IT LOCAL

    # 3. SETUP USER C (The Outsider)
    _, payload_C, _ = register_and_activate_user(
        custom_username="outsider_charlie",
        custom_email="charlie@example.com"
    )
    login_C = client.post("/api/v1/auth/login",
                          json={"identifier": payload_C["username"], "password": payload_C["password"]})
    token_C = login_C.json()["access_token"]
    headers_C = {"Authorization": f"Bearer {token_C}"}  # ◄─── KEEP IT LOCAL

    # -------------------------------------------------------------------------
    # ACTION FLOW
    # -------------------------------------------------------------------------

    # Step 1: User A creates a private project note
    note_payload = {"title": "Secret Startup Plans", "text": "Build a notes app with FastAPI."}
    # User A's headers are currently active on auth_client_A
    create_resp = auth_client_A.post("/api/v1/notes/", json=note_payload)
    assert create_resp.status_code == 201

    note_id = create_resp.json()["id"]
    assert create_resp.json()["owner"]["id"] == user_A_id  # This will now be 1 == 1!

    # Step 2: User A shares the note with User B
    share_payload = {"user_id": user_B_id, "role": "viewer"}
    share_resp = auth_client_A.put(f"/api/v1/notes/{note_id}/collaborators", json=share_payload)
    assert share_resp.status_code in [200, 201]

    # Step 3: VERIFY COLLABORATOR ACCESS — User B tries to read the shared note
    # We pass headers_B directly into the request wrapper!
    collab_get_resp = client.get(f"/api/v1/notes/{note_id}", headers=headers_B)
    assert collab_get_resp.status_code == 200
    assert collab_get_resp.json()["title"] == "Secret Startup Plans"

    # Step 4: VERIFY OUTSIDER BLOCK — User C tries to read the note but gets rejected
    # We pass headers_C directly into the request wrapper!
    outsider_get_resp = client.get(f"/api/v1/notes/{note_id}", headers=headers_C)
    assert outsider_get_resp.status_code in [403, 404], outsider_get_resp.json()

    # Step 5: VERIFY DELETION PROTECTION — User B tries to delete User A's note
    collab_delete_resp = client.delete(f"/api/v1/notes/{note_id}", headers=headers_B)
    assert collab_delete_resp.status_code in [403, 404], f"Unexpected status code: {collab_delete_resp.status_code}"


def test_owner_retains_full_privileges_after_sharing(authenticated_client, client, register_and_activate_user):
    """Ensure sharing a note doesn't alter or diminish the original owner's full CRUD access."""
    auth_client_A, user_A_id = authenticated_client

    # 1. User A creates a note
    create_resp = auth_client_A.post("/api/v1/notes/", json={"title": "Owner Power", "text": "Content"})
    note_id = create_resp.json()["id"]

    # 2. Register a collaborator (Bob)
    _, _, user_B_id = register_and_activate_user(custom_username="bob_privs", custom_email="bob_privs@example.com")

    # 3. User A shares the note
    auth_client_A.put(f"/api/v1/notes/{note_id}/collaborators", json={"user_id": user_B_id, "role": "viewer"})

    # 4. Verify Owner can still delete their own note without issue
    owner_delete_resp = auth_client_A.delete(f"/api/v1/notes/{note_id}")
    assert owner_delete_resp.status_code in [200, 204]


def test_sharing_note_with_same_user_twice_handles_gracefully(authenticated_client, register_and_activate_user):
    """Ensure re-sharing a note with an existing collaborator updates or handles it gracefully rather than exploding."""
    auth_client_A, _ = authenticated_client
    _, _, user_B_id = register_and_activate_user(custom_username="bob_double", custom_email="bob_double@example.com")

    create_resp = auth_client_A.post("/api/v1/notes/",
                                     json={"title": "Idempotency Test", "text": "Testing duplicate records."})
    note_id = create_resp.json()["id"]

    # Share 1st time
    resp1 = auth_client_A.put(f"/api/v1/notes/{note_id}/collaborators", json={"user_id": user_B_id, "role": "viewer"})
    assert resp1.status_code in [200, 201]

    # Share 2nd time (Should update role or return 200 OK cleanly)
    resp2 = auth_client_A.put(f"/api/v1/notes/{note_id}/collaborators", json={"user_id": user_B_id, "role": "editor"})
    assert resp2.status_code in [200, 204]



def test_complete_collaboration_and_revocation_lifecycle(client, authenticated_client, register_and_activate_user):
    auth_client_A, user_A_id = authenticated_client

    # Create Collaborator B
    _, payload_B, user_B_id = register_and_activate_user(custom_username="bob", custom_email="bob@example.com")
    token_B = client.post("/api/v1/auth/login", json={"identifier": "bob", "password": payload_B["password"]}).json()[
        "access_token"]
    headers_B = {"Authorization": f"Bearer {token_B}"}

    # Step 1: User A Creates Note
    note_id = auth_client_A.post("/api/v1/notes/", json={"title": "Shared Docs", "text": "Text"}).json()["id"]

    # Step 2: Add Collaborator B (PUT)
    share_resp = auth_client_A.put(f"/api/v1/notes/{note_id}/collaborators",
                                   json={"user_id": user_B_id, "role": "viewer"})
    assert share_resp.status_code == 200

    # Verify Bob can read it
    assert client.get(f"/api/v1/notes/{note_id}", headers=headers_B).status_code == 200

    # Step 3: Revoke Access (DELETE /collaborators/{user_id})
    revoke_resp = auth_client_A.delete(f"/api/v1/notes/{note_id}/collaborators/{user_B_id}")
    assert revoke_resp.status_code == 204

    # Step 4: Verify Bob is locked out instantly!
    assert client.get(f"/api/v1/notes/{note_id}", headers=headers_B).status_code in [403, 404]

