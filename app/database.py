from sqlmodel import create_engine, Session, SQLModel
import os

# Import models to ensure they are registered with SQLModel.metadata
import app.models
import app.users.models


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sigdt.db")

# Fix for Railway/Heroku postgres URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True if "sqlite" in DATABASE_URL else False)

def get_session():
    with Session(engine) as session:
        yield session

def init_test_db_schema():
    SQLModel.metadata.create_all(engine)
