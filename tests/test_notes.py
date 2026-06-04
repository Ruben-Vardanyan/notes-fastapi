# tests/test_notes.py
import pytest
from app.models.base import Note, NoteCollaborator
from app.models.note_collaborator import CollaborationRole


def test_create_and_read_note(authenticated_client):
    """Test that a logged-in user can cleanly create a note and fetch it by ID."""
    payload = {
        "title": "Pytest Architecture",
        "text": "Automated testing turns refactoring into a stress-free game."
    }

    # 1. Assert Creation
    create_response = authenticated_client.post("/api/v1/notes/", json=payload)
    assert create_response.status_code == 201

    note_data = create_response.json()
    assert note_data["title"] == payload["title"]
    assert "id" in note_data

    # 2. Assert Fetching by ID
    note_id = note_data["id"]
    get_response = authenticated_client.get(f"/api/v1/notes/{note_id}")
    assert get_response.status_code == 200
    assert get_response.json()["text"] == payload["text"]


def test_notes_feed_text_search(authenticated_client):
    """Test that the text search query (?search=...) filters contents accurately."""
    # Seed two notes into our temporary memory sandbox
    authenticated_client.post("/api/v1/notes/", json={"title": "Grocery Shopping", "text": "Apples and milk"})
    authenticated_client.post("/api/v1/notes/", json={"title": "Python Backend Tips", "text": "FastAPI rules"})

    # Search for "python" (Case-insensitive verification)
    response = authenticated_client.get("/api/v1/notes/?search=python")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Python Backend Tips"


def test_notes_feed_multi_option_filter(authenticated_client, db_session):
    """
    Test that our advanced or_(*conditions) filter engine correctly segregates
    owned notes from collaboration scopes.
    """
    # 1. Create a note owned by our authenticated client user
    my_note_res = authenticated_client.post("/api/v1/notes/", json={
        "title": "My Personal Secrets",
        "text": "Keep out!"
    })
    assert my_note_res.status_code == 201

    # 2. Case A: Request ONLY notes we own
    owned_response = authenticated_client.get("/api/v1/notes/?filter_by=owned")
    assert owned_response.status_code == 200
    assert len(owned_response.json()) == 1
    assert owned_response.json()[0]["title"] == "My Personal Secrets"

    # 3. Case B: Request ONLY notes where we are an 'editor'
    # Since we haven't been added as a collaborator to any notes yet, this should return empty!
    editor_response = authenticated_client.get("/api/v1/notes/?filter_by=editor")
    assert editor_response.status_code == 200
    assert len(editor_response.json()) == 0  # Proves data isolation works perfectly!


def test_note_update_delete(authenticated_client, db_session):
    my_note_res = authenticated_client.post("/api/v1/notes/", json={
        "title": "My Personal Secrets",
        "text": "Keep out!"
    })

    assert my_note_res.status_code == 201
    data = my_note_res.json()
    assert "id" in data
    note_id = data['id']  # Save the ID safely

    # Test Update (PATCH)
    updated_res = authenticated_client.patch(f"/api/v1/notes/{note_id}", json={
        "title": "Edited",
        "text": "Keep out! 2"
    })
    assert updated_res.status_code == 200
    assert updated_res.json()["title"] == "Edited"
    assert updated_res.json()["text"] == "Keep out! 2"

    # Test Delete (DELETE)
    delete_res = authenticated_client.delete(f"/api/v1/notes/{note_id}")
    assert delete_res.status_code == 204

    # ─── THE PRO MOVE: Assert the resource is genuinely gone ───
    ghost_res = authenticated_client.get(f"/api/v1/notes/{note_id}")
    assert ghost_res.status_code == 404


def test_note_collaboration_sharing_lifecycle(authenticated_client, client, db_session):
    create_res = authenticated_client.post("/api/v1/notes/", json={
        "title": "Shared Strategy",
        "text": "Top secret collaborator text blueprint."
    })

    assert create_res.status_code == 201
    note_id = create_res.json()["id"]

    user_b_payload = {
        "username": "collaborator_bob",
        "email": "bob@example.com",
        "password": "SecurePassword123!"
    }
    reg_b_res = client.post("/api/v1/auth/register", json=user_b_payload)
    assert reg_b_res.status_code == 201
    user_b_id = reg_b_res.json()["user"]["id"]
    bob_token = reg_b_res.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Force activate User B in our database sandbox to bypass email verification
    from app.models.base import User
    bob_record = db_session.query(User).filter(User.id == user_b_id).first()
    bob_record.is_active = True
    db_session.commit()

    share_payload = {
        "user_id": user_b_id,
        "role": CollaborationRole.EDITOR.value  # Adding Bob as an Editor
    }
    share_res = authenticated_client.put(
        f"/api/v1/notes/{note_id}/collaborators",
        json=share_payload
    )

    assert share_res.status_code == 200 or share_res.status_code == 201

    bob_owned_res = client.get("/api/v1/notes/?filter_by=owned", headers=bob_headers)
    assert bob_owned_res.status_code == 200
    assert len(bob_owned_res.json()) == 0

    # Bob checks notes where he is an editor (Should be 1!)
    bob_editor_res = client.get("/api/v1/notes/?filter_by=editor", headers=bob_headers)
    assert bob_editor_res.status_code == 200
    assert len(bob_editor_res.json()) == 1
    assert bob_editor_res.json()[0]["title"] == "Shared Strategy"

    # Confirm our nested user response schema we fixed earlier works perfectly!
    assert "user" in bob_editor_res.json()[0]["collaborators"][0]

    ghost_res = authenticated_client.delete(
        f"/api/v1/notes/{note_id}/collaborators/{user_b_id}",
    )

    assert ghost_res.status_code == 204

    final_res = authenticated_client.get(
        f"/api/v1/notes/{note_id}"
    )

    assert final_res.status_code == 200
    data = final_res.json()
    assert len(data["collaborators"]) == 0


