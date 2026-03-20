from sqlmodel import create_engine, Session, SQLModel
import os

# Import all models here so that SQLModel can discover them
from app.models import Diretiva
from app.users.models import User


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sigdt.db")

engine = create_engine(DATABASE_URL, echo=True if "sqlite" in DATABASE_URL else False)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
