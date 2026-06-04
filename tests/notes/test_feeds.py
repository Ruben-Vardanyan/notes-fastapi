# tests/notes/test_feeds.py
import pytest


def test_feed_returns_combined_or_owned_notes_only(authenticated_client, register_and_activate_user, client):
    """Ensure the notes feed dynamically aggregates the correct scoped notes for the user."""
    auth_client_A, user_A_id = authenticated_client

    # 1. User A creates two distinct notes
    auth_client_A.post("/api/v1/notes/", json={"title": "Python Architecture", "text": "Deep dive into FastAPI tools."})
    auth_client_A.post("/api/v1/notes/", json={"title": "Cooking Recipes", "text": "How to make the perfect lasagna."})

    # 2. Get User A's feed index
    # Adjust URL path to match your actual feed endpoint (e.g., /api/v1/notes/ or /api/v1/notes/feed)
    feed_resp = auth_client_A.get("/api/v1/notes/")
    assert feed_resp.status_code == 200

    feed_data = feed_resp.json()
    # Confirm User A sees their own notes
    assert len(feed_data) >= 2


def test_feed_search_query_filtering(authenticated_client):
    """Test that passing a search term (?q= or ?search=) filters the feed payload correctly."""
    auth_client, _ = authenticated_client

    # 1. Seed targeted notes
    auth_client.post("/api/v1/notes/",
                     json={"title": "Kafka Cluster Setup", "text": "Production event streaming settings."})
    auth_client.post("/api/v1/notes/", json={"title": "Grocery Shopping List", "text": "Buy milk, eggs, and bread."})

    # 2. Search for the streaming cluster note
    # Adjust query parameter key ('q', 'search', etc.) to match your backend filtering logic
    search_resp = auth_client.get("/api/v1/notes/?search=Kafka")
    assert search_resp.status_code == 200

    search_data = search_resp.json()

    # Assert filtering isolated the targeted record
    assert len(search_data) == 1
    assert "Kafka" in search_data[0]["title"]


def test_feed_array_filter_by_parameters(authenticated_client):
    """Verify multi-option filter array parsing query strings."""
    auth_client, _ = authenticated_client

    # Seed an owned note
    auth_client.post("/api/v1/notes/", json={"title": "My Owned Note", "text": "Content"})

    # Fetch feed filtering strictly for roles the user doesn't have yet (e.g., viewer)
    # Testing query list string generation format: ?filter_by=viewer
    response = auth_client.get("/api/v1/notes/?filter_by=viewer")
    assert response.status_code == 200

    # Owned note should be filtered out from a strict 'viewer' role list
    assert len(response.json()) == 0


def test_feed_combining_multiple_explicit_filters(authenticated_client, client, register_and_activate_user):
    """Verify that passing multiple filter parameters aggregates the exact intersection of notes."""
    auth_client_A, user_A_id = authenticated_client

    # 1. Create User B (The Collaborator)
    _, payload_B, user_B_id = register_and_activate_user(custom_username="multi_bob",
                                                         custom_email="bob_multi@example.com")
    token_B = \
        client.post("/api/v1/auth/login", json={"identifier": "multi_bob", "password": payload_B["password"]}).json()[
            "access_token"]
    headers_B = {"Authorization": f"Bearer {token_B}"}

    # 2. User A creates two notes
    note_id_1 = auth_client_A.post("/api/v1/notes/", json={"title": "Shared as Editor", "text": "Content"}).json()["id"]
    note_id_2 = auth_client_A.post("/api/v1/notes/", json={"title": "Shared as Viewer", "text": "Content"}).json()["id"]

    # 3. Share note 1 as 'editor' and note 2 as 'viewer' with User B
    auth_client_A.put(f"/api/v1/notes/{note_id_1}/collaborators", json={"user_id": user_B_id, "role": "editor"})
    auth_client_A.put(f"/api/v1/notes/{note_id_2}/collaborators", json={"user_id": user_B_id, "role": "viewer"})

    # 4. User B requests their feed, filtering strictly for 'owned' and 'editor' roles
    # Note 2 (viewer) should be completely filtered out of this combination
    response = client.get("/api/v1/notes/?filter_by=owned&filter_by=editor", headers=headers_B)
    assert response.status_code == 200

    feed_data = response.json()
    assert len(feed_data) == 1
    assert feed_data[0]["title"] == "Shared as Editor"
