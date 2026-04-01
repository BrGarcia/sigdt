import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_session
import os

# Use a separate SQLite file for tests or in-memory
# In-memory is faster but some features (like multi-connection) might behave differently
DATABASE_URL = "sqlite:///./test_sigdt.db"

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    if os.path.exists("test_sigdt.db"):
        os.remove("test_sigdt.db")

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
