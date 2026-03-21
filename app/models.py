from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Text, UniqueConstraint
from datetime import datetime, timezone

class Aeronave(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    matricula: str = Field(index=True, unique=True)
    numero_serie: str = Field(index=True, unique=True)
    
    # Relationship: One aircraft has many directive links
    diretiva_links: List["DiretivaAeronave"] = Relationship(back_populates="aeronave")

class Diretiva(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo_diretiva: str = Field(index=True)
    fadt: str = Field(index=True, unique=True) # Unique key
    objetivo: Optional[str] = Field(default=None, sa_column=Column(Text))
    classe: Optional[str] = None # cla (M, R, O, I)
    categoria: Optional[str] = None # cat (I, U, R)
    tipo: Optional[str] = None # tipo_incorporacao
    natureza: Optional[str] = None # nat
    ordem: Optional[str] = None
    especialidade: Optional[str] = Field(default=None, index=True)
    
    # Relationship: One master directive has many links to aircraft
    aeronave_links: List["DiretivaAeronave"] = Relationship(back_populates="diretiva")

class DiretivaAeronave(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("aeronave_id", "diretiva_id"),)
    
    id: Optional[int] = Field(default=None, primary_key=True)
    aeronave_id: int = Field(foreign_key="aeronave.id")
    diretiva_id: int = Field(foreign_key="diretiva.id")
    
    status: Optional[str] = Field(default="Pendente")
    data_aplicacao: Optional[datetime] = None
    data_status: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    ordem_aplicada: Optional[str] = None
    observacao: Optional[str] = Field(default=None, sa_column=Column(Text))
    pdf_path: Optional[str] = None
    
    # GUT Matrix fields (specific to this aircraft instance)
    tendencia: int = Field(default=3)
    gut: float = Field(default=0.0)

    # Relationships
    aeronave: Aeronave = Relationship(back_populates="diretiva_links")
    diretiva: Diretiva = Relationship(back_populates="aeronave_links")

    def calculate_gut(self):
        # Mappings based on ESPECIFICACOES.md
        g_map = {"M": 5, "R": 4, "O": 2, "I": 1}
        u_map = {"I": 5, "U": 4, "R": 2}
        
        g = g_map.get(self.diretiva.classe if self.diretiva else "I", 1)
        u = u_map.get(self.diretiva.categoria if self.diretiva else "R", 2)
        t = self.tendencia
        
        self.gut = g * u * t
        return self.gut
