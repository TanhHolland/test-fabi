"""Redis cache invalidation tests."""

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
async def test_cache_invalidates_on_create(client: AsyncClient):
    """Test that cache is invalidated after creating a new todo."""
    token = await get_auth_token(client, "cache1@example.com")

    # Initial request to populate cache
    response1 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    initial_count = len(response1.json()["items"])

    # Create a new todo (should invalidate cache)
    await client.post(
        "/api/v1/todos",
        json={"title": "New Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Request again - should show updated data, not cached data
    response2 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    new_count = len(response2.json()["items"])
    
    assert new_count == initial_count + 1


@pytest.mark.asyncio
async def test_cache_invalidates_on_update(client: AsyncClient):
    """Test that cache is invalidated after updating a todo."""
    token = await get_auth_token(client, "cache2@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get list to populate cache
    response1 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    original_title = response1.json()["items"][0]["title"]
    assert original_title == "Original Title"

    # Update the todo (should invalidate cache)
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get list again - should show updated data
    response2 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    updated_title = response2.json()["items"][0]["title"]
    assert updated_title == "Updated Title"


@pytest.mark.asyncio
async def test_cache_invalidates_on_delete(client: AsyncClient):
    """Test that cache is invalidated after deleting a todo."""
    token = await get_auth_token(client, "cache3@example.com")

    # Create two todos
    create_response1 = await client.post(
        "/api/v1/todos",
        json={"title": "Todo 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response1.json()["id"]
    
    await client.post(
        "/api/v1/todos",
        json={"title": "Todo 2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get list to populate cache
    response1 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    initial_count = len(response1.json()["items"])
    assert initial_count == 2

    # Delete one todo (should invalidate cache)
    await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get list again - should show updated count
    response2 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    new_count = len(response2.json()["items"])
    assert new_count == 1


@pytest.mark.asyncio
async def test_cache_is_user_specific(client: AsyncClient):
    """Test that cache is isolated per user."""
    # Create two users
    token_a = await get_auth_token(client, "cachea@example.com")
    token_b = await get_auth_token(client, "cacheb@example.com")

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

    # Get User A's list (populate cache)
    response_a = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todos_a = response_a.json()["items"]
    
    # Get User B's list (should have separate cache)
    response_b = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todos_b = response_b.json()["items"]

    # Verify each user only sees their own todos
    assert len(todos_a) == 1
    assert todos_a[0]["title"] == "User A's Todo"
    
    assert len(todos_b) == 1
    assert todos_b[0]["title"] == "User B's Todo"
