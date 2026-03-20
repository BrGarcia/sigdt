from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.database import init_db
from sqlmodel import Session, select
from app.models import Diretiva
from app.users.models import User
from app.users import security

client = TestClient(app)

# Ensure DB is initialized
init_db()

@pytest.fixture(name="session")
def session_fixture():
    from app.database import engine
    with Session(engine) as session:
        yield session

def test_dashboard_headers():
    response = client.get("/")
    assert response.status_code == 200
    # Should contain MATRICULA
    assert "MATRICULA" in response.text
    # Should NOT contain SN / CJM in the header (we replaced it)
    assert "SN / CJM" not in response.text
    # Should NOT contain GUT in the header
    assert "GUT" not in response.text

def test_export_xlsx_requires_auth():
    response = client.get("/export/xlsx")
    # Should redirect to login or return 401/403
    assert response.status_code in [401, 403]

def test_directive_details_has_especialidade():
    # We need a directive in the DB
    from app.database import engine
    with Session(engine) as session:
        d = Diretiva(sn_cjm="TEST-SN", diretiva_tecnica="DT-TEST", pn="PN-TEST", matr="MATR-TEST")
        session.add(d)
        session.commit()
        session.refresh(d)
        d_id = d.id

    response = client.get(f"/directives/{d_id}")
    assert response.status_code == 200
    assert "Especialidade:" in response.text

def test_directive_details_edit_fields_as_admin():
    # We need a directive and an admin user
    from app.database import engine
    with Session(engine) as session:
        # Create admin if not exists
        admin = session.exec(select(User).where(User.username == "admin_test_2")).first()
        if not admin:
            admin = User(username="admin_test_2", email="admin_test_2@example.com", hashed_password="hashed", role="admin")
            session.add(admin)
        
        d = Diretiva(sn_cjm="TEST-SN-3", diretiva_tecnica="DT-TEST-3", pn="PN-TEST-3", matr="MATR-TEST-3")
        session.add(d)
        session.commit()
        session.refresh(d)
        d_id = d.id

    # Mock login
    token = security.create_access_token(data={"sub": "admin_test_2"})
    client.cookies.set("access_token", token)

    response = client.get(f"/directives/{d_id}")
    assert response.status_code == 200
    assert "Especialidade Responsável" in response.text
    assert "Anexar Documentação (PDF)" in response.text
