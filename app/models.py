from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Text, UniqueConstraint, String
from datetime import datetime, timezone
import enum

# --- MODELOS ---

class StatusDiretiva(str, enum.Enum):
    PENDENTE = "Pendente"
    EM_ANDAMENTO = "Em andamento"
    CONCLUIDA = "Concluída"
    NAO_APLICAVEL = "Não aplicável"

class Aeronave(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    matricula: str = Field(index=True, unique=True)
    numero_serie: str = Field(index=True, unique=True)
    
    # Relationship: One aircraft has many directive links
    item_links: List["DiretivaItemAeronave"] = Relationship(back_populates="aeronave")

class DiretivaTecnica(SQLModel, table=True):
    __tablename__ = "diretiva_tecnica"
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True) # Ex: AD 2024-01
    objetivo: Optional[str] = Field(default=None, sa_column=Column(Text))
    classe: Optional[str] = None # M, R, O, I
    categoria: Optional[str] = None # I, U, R
    tipo: Optional[str] = None
    natureza: Optional[str] = None
    especialidade: Optional[str] = Field(default=None, index=True)
    ativa: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    items: List["DiretivaItem"] = Relationship(back_populates="diretiva_tecnica")

class DiretivaItem(SQLModel, table=True):
    __tablename__ = "diretiva_item"
    __table_args__ = (UniqueConstraint("diretiva_tecnica_id", "chave_item"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    diretiva_tecnica_id: int = Field(foreign_key="diretiva_tecnica.id")
    fadt: Optional[str] = Field(default=None, index=True)
    tarefa: Optional[str] = None
    ordem_referencia: Optional[str] = None
    chave_item: str = Field(index=True) # Chave técnica de deduplicação
    descricao_item: Optional[str] = Field(default=None, sa_column=Column(Text))
    ativo: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    diretiva_tecnica: DiretivaTecnica = Relationship(back_populates="items")
    aeronave_links: List["DiretivaItemAeronave"] = Relationship(back_populates="diretiva_item")

class DiretivaItemAeronave(SQLModel, table=True):
    __tablename__ = "diretiva_item_aeronave"
    __table_args__ = (UniqueConstraint("aeronave_id", "diretiva_item_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    aeronave_id: int = Field(foreign_key="aeronave.id")
    diretiva_item_id: int = Field(foreign_key="diretiva_item.id")
    
    status: str = Field(default="Pendente")
    data_aplicacao: Optional[datetime] = None
    data_status: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ordem_aplicada: Optional[str] = None
    observacao: Optional[str] = Field(default=None, sa_column=Column(Text))
    pdf_path: Optional[str] = None
    
    tendencia: int = Field(default=3)
    gut: float = Field(default=0.0)
    
    origem_status: str = Field(default="csv") # csv, manual
    ultima_referencia_snapshot: Optional[str] = None
    concluida_automaticamente: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    aeronave: Aeronave = Relationship(back_populates="item_links")
    diretiva_item: DiretivaItem = Relationship(back_populates="aeronave_links")

    def calculate_gut(self):
        g_map = {"M": 5, "R": 4, "O": 2, "I": 1}
        u_map = {"I": 5, "U": 4, "R": 2}
        
        dt = self.diretiva_item.diretiva_tecnica if self.diretiva_item else None
        g = g_map.get(dt.classe if dt else "I", 1)
        u = u_map.get(dt.categoria if dt else "R", 2)
        t = self.tendencia
        
        self.gut = g * u * t
        return self.gut
