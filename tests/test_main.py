from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.database import init_db
import os

client = TestClient(app)

def test_read_main():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_page():
    response = client.get("/login")
    assert response.status_code == 200
    assert "login" in response.text.lower()
