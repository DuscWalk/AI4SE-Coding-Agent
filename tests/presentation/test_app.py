# tests/presentation/test_app.py
"""Tests for FastAPI presentation layer."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from coding_agent.presentation.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_status_endpoint(client):
    """GET /api/status should return 200 with status key."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_sessions_list(client):
    """GET /api/sessions should return 200 with a list."""
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_credentials_status(client):
    """GET /api/credentials/status should return 200 with configured key."""
    response = client.get("/api/credentials/status")
    assert response.status_code == 200
    assert "configured" in response.json()