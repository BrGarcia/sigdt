import pandas as pd
from sqlmodel import Session, select
from app.models import Diretiva, Aeronave, DiretivaAeronave
from app.database import engine
from io import StringIO
import numpy as np

def sanitize_formula(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

def process_csv(csv_content: str):
    # The file uses ';' as separator
    df = pd.read_csv(StringIO(csv_content), sep=';', skipinitialspace=True)
    
    # Clean column names (strip spaces)
    df.columns = [c.strip() for c in df.columns]
    
    def get_val(row, col_name):
        val = row.get(col_name)
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        
        if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == '':
            return None
        return sanitize_formula(str(val).strip())

    BATCH_SIZE = 100
    with Session(engine) as session:
        for i, row in df.iterrows():
            # ... (rest of the loop remains similar but uses batch commits)
            # Implementation note: For v1.0.0-pre, let's keep the logic but ensure commit every BATCH_SIZE
            
            # (Keeping the original UPSERT logic but applying it within the session)
            # 1. Obter ou criar Aeronave (UPSERT via Matrícula)
            matricula = get_val(row, 'MATR')
            numero_serie = get_val(row, 'SN')
            
            if not matricula or not numero_serie:
                continue
                
            statement_aero = select(Aeronave).where(Aeronave.matricula == matricula)
            aeronave = session.exec(statement_aero).first()
            
            if not aeronave:
                aeronave = Aeronave(matricula=matricula, numero_serie=numero_serie)
                session.add(aeronave)
                session.flush() 
            else:
                aeronave.numero_serie = numero_serie 
                session.add(aeronave)

            # 2. Obter ou criar Diretiva Técnica (UPSERT via FADT)
            fadt = get_val(row, 'FADT')
            codigo_dt = get_val(row, 'DIRETIVA TÉCNICA')
            
            if not fadt or not codigo_dt:
                continue
                
            statement_dt = select(Diretiva).where(Diretiva.fadt == fadt)
            diretiva = session.exec(statement_dt).first()
            
            dt_data = {
                "codigo_diretiva": codigo_dt,
                "fadt": fadt,
                "objetivo": get_val(row, 'OBJETIVO'),
                "classe": get_val(row, 'CLA'),
                "categoria": get_val(row, 'CAT'),
                "tipo": get_val(row, 'TIPO INCORPORAÇÃO'),
                "natureza": get_val(row, 'NAT'),
                "ordem": get_val(row, 'ORDEM'),
            }
            
            if not diretiva:
                diretiva = Diretiva(**dt_data)
                session.add(diretiva)
                session.flush()
            else:
                for key, value in dt_data.items():
                    setattr(diretiva, key, value)
                session.add(diretiva)

            # 3. Vincular Diretiva à Aeronave (UPSERT)
            statement_link = select(DiretivaAeronave).where(
                DiretivaAeronave.aeronave_id == aeronave.id,
                DiretivaAeronave.diretiva_id == diretiva.id
            )
            link = session.exec(statement_link).first()
            
            link_data = {
                "aeronave_id": aeronave.id,
                "diretiva_id": diretiva.id,
                "status": get_val(row, 'STATUS'),
                "ordem_aplicada": get_val(row, 'ORDEM'),
                "observacao": get_val(row, 'OBSERVAÇÕES') or get_val(row, 'PJ'),
            }
            
            if not link:
                link = DiretivaAeronave(**link_data)
                link.tendencia = 3 
                session.add(link)
            else:
                for key, value in link_data.items():
                    setattr(link, key, value)
                session.add(link)
            
            link.diretiva = diretiva
            link.calculate_gut()

            if (i + 1) % BATCH_SIZE == 0:
                session.commit()

        session.commit()
    
    return len(df)
