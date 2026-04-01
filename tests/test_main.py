from fastapi.testclient import TestClient
import pytest
from app.core.config import SECRET_KEY
from jose import jwt
import time

@pytest.fixture
def authorized_client(client):
    # Bypass Gatekeeper with signed JWT
    token = jwt.encode({"access": "granted", "exp": time.time() + 36000}, SECRET_KEY, algorithm="HS256")
    client.cookies.set("gatekeeper_access", token)
    return client

def test_read_main(authorized_client):
    response = authorized_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_page(authorized_client):
    response = authorized_client.get("/login")
    assert response.status_code == 200
    assert "login" in response.text.lower()
