"""Authorization boundary tests for todos."""

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str) -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_user_cannot_access_other_user_todos(client: AsyncClient):
    """User A cannot access User B's todo by ID."""
    # Create two users
    token_a = await get_auth_token(client, "usera@example.com")
    token_b = await get_auth_token(client, "userb@example.com")

    # User B creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "User B's Todo", "description": "Private todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert create_response.status_code == 201
    todo_b_id = create_response.json()["id"]

    # User A tries to access User B's todo
    response = await client.get(
        f"/api/v1/todos/{todo_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


@pytest.mark.asyncio
async def test_user_cannot_update_other_user_todos(client: AsyncClient):
    """User A cannot update User B's todo."""
    # Create two users
    token_a = await get_auth_token(client, "usera2@example.com")
    token_b = await get_auth_token(client, "userb2@example.com")

    # User B creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "User B's Todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_b_id = create_response.json()["id"]

    # User A tries to update User B's todo
    response = await client.put(
        f"/api/v1/todos/{todo_b_id}",
        json={"title": "Hacked by User A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


@pytest.mark.asyncio
async def test_user_cannot_delete_other_user_todos(client: AsyncClient):
    """User A cannot delete User B's todo."""
    # Create two users
    token_a = await get_auth_token(client, "usera3@example.com")
    token_b = await get_auth_token(client, "userb3@example.com")

    # User B creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "User B's Todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_b_id = create_response.json()["id"]

    # User A tries to delete User B's todo
    response = await client.delete(
        f"/api/v1/todos/{todo_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_list_only_shows_own_todos(client: AsyncClient):
    """User A's todo list only contains their own todos, not User B's."""
    # Create two users
    token_a = await get_auth_token(client, "usera4@example.com")
    token_b = await get_auth_token(client, "userb4@example.com")

    # User A creates a todo
    await client.post(
        "/api/v1/todos",
        json={"title": "User A's Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B creates a todo
    await client.post(
        "/api/v1/todos",
        json={"title": "User B's Todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A gets their todo list
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    
    # Verify User A only sees their own todo
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "User A's Todo"
    assert "User B's Todo" not in [item["title"] for item in data["items"]]
