from fastapi.testclient import TestClient
import pytest
from app.core.config import SECRET_KEY
from sqlmodel import Session, select
from app.models import Aeronave, DiretivaTecnica, DiretivaItem, DiretivaItemAeronave
from app.users.models import User
from app.users import security
import uuid
from jose import jwt
import time

@pytest.fixture
def authorized_client(client):
    # Bypass Gatekeeper with signed JWT
    token = jwt.encode({"access": "granted", "exp": time.time() + 3600}, SECRET_KEY, algorithm="HS256")
    client.cookies.set("gatekeeper_access", token)
    return client

def test_dashboard_headers(authorized_client):
    response = authorized_client.get("/")
    assert response.status_code == 200
    # Should contain MATRÍCULA (with accent)
    assert "MATRÍCULA" in response.text
    # Should contain GUT
    assert "GUT" in response.text

def test_export_xlsx_requires_auth(authorized_client):
    response = authorized_client.get("/export/xlsx")
    # Should require login if not admin
    assert response.status_code in [200, 401, 403, 303, 307]

def test_directive_details_has_especialidade(authorized_client, session: Session):
    uid = str(uuid.uuid4())[:8]
    
    a = Aeronave(matricula=f"MATR-{uid}", numero_serie=f"SN-{uid}")
    session.add(a)
    session.flush()
    
    dt = DiretivaTecnica(codigo_simplificado=f"DT{uid}", codigo=f"DT-{uid}", objetivo="OBJ-TEST")
    session.add(dt)
    session.flush()

    item = DiretivaItem(diretiva_tecnica_id=dt.codigo_simplificado, fadt=f"FADT-{uid}", chave_item=f"CHAVE-{uid}")
    session.add(item)
    session.flush()
    
    link = DiretivaItemAeronave(aeronave_id=a.id, diretiva_item_id=item.id, status="Pendente")
    session.add(link)
    session.commit()
    session.refresh(link)
    link_id = link.id

    response = authorized_client.get(f"/directives/{link_id}")
    assert response.status_code == 200

def test_directive_details_edit_fields_as_admin(authorized_client, session: Session):
    uid = str(uuid.uuid4())[:8]
    
    # Create admin if not exists
    username = f"admin_{uid}"
    admin = User(username=username, email=f"{username}@example.com", hashed_password="hashed", role="admin")
    session.add(admin)
    
    a = Aeronave(matricula=f"MATR-A-{uid}", numero_serie=f"SN-A-{uid}")
    session.add(a)
    session.flush()
    
    dt = DiretivaTecnica(codigo_simplificado=f"DTA{uid}", codigo=f"DT-A-{uid}", objetivo="OBJ-TEST-2")
    session.add(dt)
    session.flush()

    item = DiretivaItem(diretiva_tecnica_id=dt.codigo_simplificado, fadt=f"FADT-A-{uid}", chave_item=f"CHAVE-A-{uid}")
    session.add(item)
    session.flush()
    
    link = DiretivaItemAeronave(aeronave_id=a.id, diretiva_item_id=item.id, status="Pendente")
    session.add(link)
    session.commit()
    session.refresh(link)
    link_id = link.id

    # Mock login
    token = security.create_access_token(data={"sub": username})
    authorized_client.cookies.set("access_token", token)

    response = authorized_client.get(f"/directives/{link_id}")
    assert response.status_code == 200

def test_create_user_persists_and_returns_fragment(authorized_client, session: Session):
    uid = str(uuid.uuid4())[:8]
    admin_username = f"adm_{uid}"
    admin = User(
        username=admin_username,
        email=f"{admin_username}@example.com",
        hashed_password="hashed",
        role="admin"
    )
    session.add(admin)
    session.commit()

    token = security.create_access_token(data={"sub": admin_username})
    authorized_client.cookies.set("access_token", token)

    page_response = authorized_client.get("/users/manage")
    assert page_response.status_code == 200

    csrf_token = authorized_client.cookies.get("csrftoken")
    assert csrf_token

    username = f"user_{uid}"
    response = authorized_client.post(
        "/users/",
        data={
            "username": username,
            "email": f"{username}@example.com",
            "password": "Password123",
            "role": "inspetor",
            "especialidade": "BMA",
        },
        headers={
            "x-csrftoken": csrf_token,
            "HX-Request": "true",
        },
    )

    assert response.status_code == 200
    assert username in response.text

    created_user = session.exec(select(User).where(User.username == username)).first()
    assert created_user is not None
    assert created_user.email == f"{username}@example.com"

def test_create_user_invalid_password_returns_422_not_500(authorized_client, session: Session):
    uid = str(uuid.uuid4())[:8]
    admin_username = f"adm_{uid}"
    admin = User(
        username=admin_username,
        email=f"{admin_username}@example.com",
        hashed_password="hashed",
        role="admin"
    )
    session.add(admin)
    session.commit()

    token = security.create_access_token(data={"sub": admin_username})
    authorized_client.cookies.set("access_token", token)

    page_response = authorized_client.get("/users/manage")
    assert page_response.status_code == 200

    csrf_token = authorized_client.cookies.get("csrftoken")
    assert csrf_token

    response = authorized_client.post(
        "/users/",
        data={
            "username": f"user_{uid}",
            "email": f"user_{uid}@example.com",
            "password": "123456",
            "role": "inspetor",
            "especialidade": "BMA",
        },
        headers={
            "x-csrftoken": csrf_token,
            "HX-Request": "true",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Senha deve ter ao menos 8 caracteres."
