from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    hashed_password: str
    role: str = Field(default="user") # "user" or "admin"
    especialidade: Optional[str] = Field(default=None) # ELETRÔNICA;ELÉTRICA;CÉLULA;HIDRÁULICA;MOTORES;EQV
