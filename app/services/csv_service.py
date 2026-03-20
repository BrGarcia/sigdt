import pandas as pd
from sqlmodel import Session, select
from app.models import Diretiva
from app.database import engine
from io import StringIO
import numpy as np

def process_csv(csv_content: str):
    # The file uses ';' as separator
    # We use engine='python' to better handle some edge cases with separators
    df = pd.read_csv(StringIO(csv_content), sep=';', skipinitialspace=True)
    
    # Clean column names (strip spaces)
    df.columns = [c.strip() for c in df.columns]
    
    def get_val(row, col_name):
        # Try exact match first
        val = row.get(col_name)
        # If it's a Series (due to duplicate column names not being mangled correctly or other issues)
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        
        if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == '':
            return None
        return str(val).strip()

    with Session(engine) as session:
        for i, row in df.iterrows():
            # Extract unique keys
            sn_cjm = get_val(row, 'SN CJM')
            if not sn_cjm:
                sn_cjm = get_val(row, 'SN')
            
            diretiva_tecnica = get_val(row, 'DIRETIVA TÉCNICA')
            
            if not sn_cjm or not diretiva_tecnica:
                continue
            
            # Find if it already exists
            statement = select(Diretiva).where(
                Diretiva.sn_cjm == sn_cjm,
                Diretiva.diretiva_tecnica == diretiva_tecnica
            )
            existing_diretiva = session.exec(statement).first()
            
            # Map data
            data = {
                "pn": get_val(row, 'PN'),
                "cff": get_val(row, 'CFF'),
                "matr": get_val(row, 'MATR'),
                "sn": get_val(row, 'SN'),
                "unidade": get_val(row, 'UNIDADE'),
                "status": get_val(row, 'STATUS'),
                "pj": get_val(row, 'PJ'),
                "sn_cjm": sn_cjm,
                "diretiva_tecnica": diretiva_tecnica,
                "fadt": get_val(row, 'FADT'),
                "nat": get_val(row, 'NAT'),
                "ordem": get_val(row, 'ORDEM'),
                "cla": get_val(row, 'CLA'),
                "cat": get_val(row, 'CAT'),
                "tipo_incorporacao": get_val(row, 'TIPO INCORPORAÇÃO'),
                "prazo_incorporacao": get_val(row, 'PRAZO INCORPORAÇÃO'),
                "tarefa": get_val(row, 'TAREFA'),
                "horas": get_val(row, 'HORAS'),
                "rescisao": get_val(row, 'RESCISÃO'),
                "objetivo": get_val(row, 'OBJETIVO'),
            }
            
            if existing_diretiva:
                for key, value in data.items():
                    setattr(existing_diretiva, key, value)
                existing_diretiva.calculate_gut()
                session.add(existing_diretiva)
            else:
                new_diretiva = Diretiva(**data)
                new_diretiva.tendencia = 3
                new_diretiva.calculate_gut()
                session.add(new_diretiva)
        
        session.commit()
    
    return len(df)
