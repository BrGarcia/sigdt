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
    df = pd.read_csv(StringIO(csv_content), sep=';', skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    
    def get_val(row, col_name):
        val = row.get(col_name)
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        
        if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == '':
            return None
        return sanitize_formula(str(val).strip())

    BATCH_SIZE = 500
    with Session(engine) as session:
        # 1. Pre-Cache do Banco
        todas_aeronaves = session.exec(select(Aeronave)).all()
        aero_cache = {a.matricula: a for a in todas_aeronaves}

        todas_diretivas = session.exec(select(Diretiva)).all()
        dt_cache = {d.fadt: d for d in todas_diretivas}

        todos_links = session.exec(select(DiretivaAeronave)).all()
        link_cache = {(l.aeronave_id, l.diretiva_id): l for l in todos_links}

        for i, row in df.iterrows():
            matricula = get_val(row, 'MATR')
            numero_serie = get_val(row, 'SN')
            
            if not matricula or not numero_serie:
                continue

            # Aeronave Upsert (Cache)
            aeronave = aero_cache.get(matricula)
            if not aeronave:
                aeronave = Aeronave(matricula=matricula, numero_serie=numero_serie)
                session.add(aeronave)
                session.flush() # Necessário flush para obter o ID
                aero_cache[matricula] = aeronave
            else:
                if aeronave.numero_serie != numero_serie:
                    aeronave.numero_serie = numero_serie
                    session.add(aeronave)

            fadt = get_val(row, 'FADT')
            codigo_dt = get_val(row, 'DIRETIVA TÉCNICA')
            
            if not fadt or not codigo_dt:
                continue

            dt_data = {
                "codigo_diretiva": codigo_dt,
                "fadt": fadt,
                "objetivo": get_val(row, 'OBJETIVO'),
                "classe": get_val(row, 'CLA'),
                "categoria": get_val(row, 'CAT'),
                "tipo": get_val(row, 'TIPO INCORPORAÇÃO'),
                "natureza": get_val(row, 'NAT'),
                "ordem": get_val(row, 'ORDEM'),
                "especialidade": get_val(row, 'ESPECIALIDADE') # Adicionado para garantir suporte se houver
            }

            # Diretiva Upsert (Cache)
            diretiva = dt_cache.get(fadt)
            if not diretiva:
                diretiva = Diretiva(**dt_data)
                session.add(diretiva)
                session.flush()
                dt_cache[fadt] = diretiva
            else:
                for key, value in dt_data.items():
                    setattr(diretiva, key, value)
                session.add(diretiva)

            # Link Upsert (Cache)
            cache_key = (aeronave.id, diretiva.id)
            link = link_cache.get(cache_key)
            
            link_data = {
                "aeronave_id": aeronave.id,
                "diretiva_id": diretiva.id,
                "status": get_val(row, 'STATUS') or "Pendente",
                "ordem_aplicada": get_val(row, 'ORDEM'),
                "observacao": get_val(row, 'OBSERVAÇÕES') or get_val(row, 'PJ'),
            }

            if not link:
                link = DiretivaAeronave(**link_data)
                link.tendencia = 3
                session.add(link)
                link_cache[cache_key] = link
            else:
                for key, value in link_data.items():
                    if value is not None:
                        setattr(link, key, value)
                session.add(link)

            link.diretiva = diretiva
            link.calculate_gut()

            if (i + 1) % BATCH_SIZE == 0:
                session.commit()

        session.commit()
    
    return len(df)
