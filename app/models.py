from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from datetime import datetime

class Diretiva(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pn: Optional[str] = None
    cff: Optional[str] = None
    matr: Optional[str] = None
    sn: Optional[str] = None
    unidade: Optional[str] = None
    status: Optional[str] = None
    pj: Optional[str] = None
    sn_cjm: str = Field(index=True) # Unique key part
    diretiva_tecnica: str = Field(index=True) # Unique key part
    fadt: Optional[str] = None
    nat: Optional[str] = None
    ordem: Optional[str] = None
    cla: Optional[str] = None # Gravity Code (M, R, O, I)
    cat: Optional[str] = None # Urgency Code (I, U, R)
    tipo_incorporacao: Optional[str] = None
    prazo_incorporacao: Optional[str] = None
    tarefa: Optional[str] = None
    horas: Optional[str] = None
    rescisao: Optional[str] = None
    objetivo: Optional[str] = None
    observacoes: Optional[str] = Field(default=None, sa_column=Column(Text))
    ultima_modificacao: Optional[datetime] = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})
    
    # GUT Matrix fields
    tendencia: int = Field(default=3)
    gut: float = Field(default=0.0)
    especialidade: Optional[str] = Field(default=None, index=True) # ELETRONICA;ELETRICA;CÉLULA;HIDRAULICA;EQV
    pdf_path: Optional[str] = None

    def calculate_gut(self):
        # Mappings based on ESPECIFICACOES.md
        g_map = {"M": 5, "R": 4, "O": 2, "I": 1}
        u_map = {"I": 5, "U": 4, "R": 2}
        
        g = g_map.get(self.cla, 1)
        u = u_map.get(self.cat, 2)
        t = self.tendencia
        
        self.gut = g * u * t
        return self.gut
