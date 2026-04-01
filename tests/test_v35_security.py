from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.config import SECRET_KEY
from jose import jwt
import time
import os
from app.models import StatusDiretiva
from app.users.schemas import UserCreate
from pydantic import ValidationError

client = TestClient(app)

def get_gatekeeper_token():
    return jwt.encode({"access": "granted", "exp": time.time() + 3600}, SECRET_KEY, algorithm="HS256")

def get_csrf_token():
    client.get("/gatekeeper")
    token = client.cookies.get("csrftoken")
    return token or ""

def test_gatekeeper_unauthorized_redirect():
    client.cookies.clear()
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/gatekeeper" in response.headers["location"]

def test_gatekeeper_invalid_password():
    csrf_token = get_csrf_token()
    response = client.post("/gatekeeper", data={"password": "wrong_password"}, headers={"x-csrftoken": csrf_token}, follow_redirects=False)
    assert response.status_code == 303
    assert "/gatekeeper?error=1" in response.headers["location"]

def test_gatekeeper_valid_password():
    csrf_token = get_csrf_token()
    password = os.getenv("GATEKEEPER_PASSWORD")
    response = client.post("/gatekeeper", data={"password": password}, headers={"x-csrftoken": csrf_token}, follow_redirects=False)
    assert response.status_code == 303
    assert "gatekeeper_access" in response.cookies
    
    # Verify token
    token = response.cookies["gatekeeper_access"]
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    assert payload["access"] == "granted"

def test_user_create_validation():
    # Invalid username (too short)
    with pytest.raises(ValidationError):
        UserCreate(username="ab", email="test@example.com", password="password123")
    
    # Invalid username (special chars)
    with pytest.raises(ValidationError):
        UserCreate(username="user!", email="test@example.com", password="password123")
    
    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(username="valid_user", email="invalid-email", password="password123")
    
    # Invalid password (too short)
    with pytest.raises(ValidationError):
        UserCreate(username="valid_user", email="test@example.com", password="123")
    
    # Valid user
    user = UserCreate(username="valid_user", email="test@example.com", password="password123")
    assert user.username == "valid_user"

def test_status_diretiva_enum():
    assert "Pendente" in [s.value for s in StatusDiretiva]
    assert "Concluída" in [s.value for s in StatusDiretiva]
    assert "Não aplicável" in [s.value for s in StatusDiretiva]

def test_rate_limiting_gatekeeper():
    # 6 attempts to trigger rate limit
    for _ in range(5):
        csrf_token = get_csrf_token()
        client.post("/gatekeeper", data={"password": "wrong"}, headers={"x-csrftoken": csrf_token})
    
    csrf_token = get_csrf_token()
    response = client.post("/gatekeeper", data={"password": "wrong"}, headers={"x-csrftoken": csrf_token})
    assert response.status_code == 429
    assert "Muitas tentativas" in response.json()["detail"]

def test_protected_route_with_valid_jwt():
    token = get_gatekeeper_token()
    client.cookies.set("gatekeeper_access", token)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
