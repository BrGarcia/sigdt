from sqlmodel import Session, select
from . import models, schemas, security

def get_user(db: Session, username: str):
    statement = select(models.User).where(models.User.username == username)
    return db.exec(statement).first()

def get_user_by_email(db: Session, email: str):
    statement = select(models.User).where(models.User.email == email)
    return db.exec(statement).first()

def create_user(db: Session, user: schemas.UserCreate, role: str = "user"):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=role,
        especialidade=user.especialidade
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
