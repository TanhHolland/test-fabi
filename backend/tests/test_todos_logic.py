"""Business logic tests for todo operations."""

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
async def test_todo_boolean_toggle_persistence(client: AsyncClient):
    """Test that boolean toggle (completed: true → false) persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Test", "completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]
    assert create_response.json()["completed"] is False

    # Toggle to completed
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["completed"] is True

    # Get the todo to verify persistence
    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.json()["completed"] is True

    # Toggle back to not completed
    update_response2 = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response2.status_code == 200
    assert update_response2.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_other_fields(client: AsyncClient):
    """Test that partial update doesn't delete non-updated fields."""
    token = await get_auth_token(client, "partial@example.com")

    # Create a todo with all fields
    create_response = await client.post(
        "/api/v1/todos",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "completed": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Partial update: only update title
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    
    # Verify description is preserved
    updated_todo = update_response.json()
    assert updated_todo["title"] == "Updated Title"
    assert updated_todo["description"] == "Original Description"
    assert updated_todo["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_only_description(client: AsyncClient):
    """Test updating only description preserves title and completed status."""
    token = await get_auth_token(client, "partial2@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={
            "title": "Original Title",
            "description": "Original Description",
            "completed": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Partial update: only update description
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"description": "Updated Description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    
    updated_todo = update_response.json()
    assert updated_todo["title"] == "Original Title"
    assert updated_todo["description"] == "Updated Description"
    assert updated_todo["completed"] is True


@pytest.mark.asyncio
async def test_create_todo_with_empty_description(client: AsyncClient):
    """Test creating todo with empty/null description."""
    token = await get_auth_token(client, "emptydesc@example.com")

    # Create todo without description
    response = await client.post(
        "/api/v1/todos",
        json={"title": "No Description Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "No Description Todo"
    assert data["description"] is None or data["description"] == ""


@pytest.mark.asyncio
async def test_pagination_works_correctly(client: AsyncClient):
    """Test that pagination returns correct number of items."""
    token = await get_auth_token(client, "pagination@example.com")

    # Create 25 todos
    for i in range(25):
        await client.post(
            "/api/v1/todos",
            json={"title": f"Todo {i+1}"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Get first page (size=20)
    response = await client.get(
        "/api/v1/todos?page=1&size=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert len(data["items"]) == 20
    assert data["total"] == 25
    assert data["page"] == 1

    # Get second page
    response2 = await client.get(
        "/api/v1/todos?page=2&size=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    data2 = response2.json()
    assert len(data2["items"]) == 5
    assert data2["total"] == 25
    assert data2["page"] == 2
