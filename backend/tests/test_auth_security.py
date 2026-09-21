"""Authentication security tests."""

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings


@pytest.mark.asyncio
async def test_invalid_token_rejected(client: AsyncClient):
    """Test that invalid/tampered tokens are rejected."""
    # Try to access protected endpoint with invalid token
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": "Bearer invalid_token_here"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_token_rejected(client: AsyncClient):
    """Test that requests without token are rejected."""
    response = await client.get("/api/v1/todos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    """Test that expired tokens are rejected."""
    from datetime import datetime, timedelta, timezone
    
    # Create an expired token
    expired_payload = {
        "sub": "test-user-id",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
        "type": "access"
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    # Try to access protected endpoint with expired token
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_password_login_fails(client: AsyncClient):
    """Test that login with wrong password fails."""
    # Register a user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "correct_password"},
    )

    # Try to login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient):
    """Test that registering with existing email fails."""
    # Register a user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    # Try to register again with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password456"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_token_contains_correct_claims(client: AsyncClient):
    """Test that generated tokens contain required claims."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "claims@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    
    token = response.json()["access_token"]
    
    # Decode without verification to inspect claims
    decoded = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"verify_exp": False}
    )
    
    assert "sub" in decoded  # Subject (user ID)
    assert "exp" in decoded  # Expiration
    assert "type" in decoded  # Token type
    assert decoded["type"] == "access"
