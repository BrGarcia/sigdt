from fastapi.testclient import TestClient
import pytest
from app.main import app, SECRET_KEY
from app.database import init_db
import os
from jose import jwt
import time

client = TestClient(app)
# Bypass Gatekeeper with signed JWT
token = jwt.encode({"access": "granted", "exp": time.time() + 3600}, SECRET_KEY, algorithm="HS256")
client.cookies.set("gatekeeper_access", token)

def test_read_main():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_page():
    response = client.get("/login")
    assert response.status_code == 200
    assert "login" in response.text.lower()
