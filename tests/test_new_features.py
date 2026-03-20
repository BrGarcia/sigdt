from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.database import init_db
from sqlmodel import Session, select
from app.models import Diretiva, Aeronave, DiretivaAeronave
from app.users.models import User
from app.users import security
import uuid

client = TestClient(app)
# Bypass Gatekeeper
client.cookies.set("gatekeeper_access", "granted")

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
    # Should contain MATRÍCULA (with accent)
    assert "MATRÍCULA" in response.text
    # Should contain GUT
    assert "GUT" in response.text

def test_export_xlsx_requires_auth():
    response = client.get("/export/xlsx")
    # Should return 401/403
    assert response.status_code in [401, 403]

def test_directive_details_has_especialidade():
    # We need a relational structure in the DB
    # Use UUID to avoid unique constraint violations
    uid = str(uuid.uuid4())[:8]
    from app.database import engine
    with Session(engine) as session:
        a = Aeronave(matricula=f"MATR-{uid}", numero_serie=f"SN-{uid}")
        session.add(a)
        session.flush()
        
        d = Diretiva(codigo_diretiva=f"DT-{uid}", fadt=f"FADT-{uid}", objetivo="OBJ-TEST")
        session.add(d)
        session.flush()
        
        link = DiretivaAeronave(aeronave_id=a.id, diretiva_id=d.id, status="Pendente")
        session.add(link)
        session.commit()
        session.refresh(link)
        link_id = link.id

    response = client.get(f"/directives/{link_id}")
    assert response.status_code == 200
    assert "Especialidade:" in response.text

def test_directive_details_edit_fields_as_admin():
    # We need a relational structure and an admin user
    uid = str(uuid.uuid4())[:8]
    from app.database import engine
    with Session(engine) as session:
        # Create admin if not exists
        username = f"admin_{uid}"
        admin = User(username=username, email=f"{username}@example.com", hashed_password="hashed", role="admin")
        session.add(admin)
        
        a = Aeronave(matricula=f"MATR-A-{uid}", numero_serie=f"SN-A-{uid}")
        session.add(a)
        session.flush()
        
        d = Diretiva(codigo_diretiva=f"DT-A-{uid}", fadt=f"FADT-A-{uid}", objetivo="OBJ-TEST-2")
        session.add(d)
        session.flush()
        
        link = DiretivaAeronave(aeronave_id=a.id, diretiva_id=d.id, status="Pendente")
        session.add(link)
        session.commit()
        session.refresh(link)
        link_id = link.id

    # Mock login
    token = security.create_access_token(data={"sub": username})
    client.cookies.set("access_token", token)

    response = client.get(f"/directives/{link_id}")
    assert response.status_code == 200
    assert "Especialidade Responsável" in response.text
    assert "Anexar Comprovante (PDF)" in response.text
