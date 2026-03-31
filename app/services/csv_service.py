import pandas as pd
from sqlmodel import Session, select
from app.models import DiretivaTecnica, DiretivaItem, DiretivaItemAeronave, Aeronave
from app.database import engine
from io import StringIO
from datetime import datetime, timezone
from typing import Optional

def sanitize_formula(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

def generate_chave_item(codigo_dt: str, fadt: Optional[str], tarefa: Optional[str], ordem: Optional[str]) -> str:
    """Gera uma chave determinística para deduplicação do item."""
    c = str(codigo_dt or "").strip().upper()
    f = str(fadt or "").strip().upper()
    t = str(tarefa or "").strip().upper()
    o = str(ordem or "").strip().upper()
    return f"{c}|{f}|{t}|{o}"

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

    snapshot_ts = datetime.now(timezone.utc).isoformat()
    processed_count = 0
    
    with Session(engine) as session:
        # Cache de Aeronaves e Mestres para performance
        aero_cache = {a.matricula: a for a in session.exec(select(Aeronave)).all()}
        dt_cache = {d.codigo: d for d in session.exec(select(DiretivaTecnica)).all()}
        
        # Identificar aeronaves presentes no CSV para aplicar snapshot logic depois
        matriculas_no_csv = df['MATR'].dropna().unique()
        links_processados_ids = []

        for i, row in df.iterrows():
            matricula = get_val(row, 'MATR')
            sn = get_val(row, 'SN')
            if not matricula or not sn: continue

            # 1. Aeronave Upsert
            aeronave = aero_cache.get(matricula)
            if not aeronave:
                aeronave = Aeronave(matricula=matricula, numero_serie=sn)
                session.add(aeronave)
                session.flush()
                aero_cache[matricula] = aeronave
            elif aeronave.numero_serie != sn:
                aeronave.numero_serie = sn
                session.add(aeronave)

            codigo_dt = get_val(row, 'DIRETIVA TÉCNICA')
            if not codigo_dt: continue

            # 2. DiretivaTecnica Upsert (Mestre)
            dt = dt_cache.get(codigo_dt)
            dt_data = {
                "codigo": codigo_dt,
                "objetivo": get_val(row, 'OBJETIVO'),
                "classe": get_val(row, 'CLA'),
                "categoria": get_val(row, 'CAT'),
                "tipo": get_val(row, 'TIPO INCORPORAÇÃO'),
                "natureza": get_val(row, 'NAT'),
                "especialidade": get_val(row, 'ESPECIALIDADE'),
                "updated_at": datetime.now(timezone.utc)
            }
            if not dt:
                dt = DiretivaTecnica(**dt_data)
                session.add(dt)
                session.flush()
                dt_cache[codigo_dt] = dt
            else:
                for key, value in dt_data.items():
                    setattr(dt, key, value)
                session.add(dt)

            # 3. DiretivaItem Upsert (Subordinado)
            fadt = get_val(row, 'FADT')
            tarefa = get_val(row, 'TAREFA') # Coluna opcional no CSV, tratar se existir
            ordem_ref = get_val(row, 'ORDEM')
            chave = generate_chave_item(codigo_dt, fadt, tarefa, ordem_ref)
            
            # Busca item no banco (pode haver muitos itens, cache local por mestre se necessário)
            item = session.exec(
                select(DiretivaItem).where(
                    DiretivaItem.diretiva_tecnica_id == dt.id,
                    DiretivaItem.chave_item == chave
                )
            ).first()

            if not item:
                item = DiretivaItem(
                    diretiva_tecnica_id=dt.id,
                    fadt=fadt,
                    tarefa=tarefa,
                    ordem_referencia=ordem_ref,
                    chave_item=chave,
                    descricao_item=dt.objetivo
                )
                session.add(item)
                session.flush()

            # 4. DiretivaItemAeronave Upsert (Estado Operacional)
            link = session.exec(
                select(DiretivaItemAeronave).where(
                    DiretivaItemAeronave.aeronave_id == aeronave.id,
                    DiretivaItemAeronave.diretiva_item_id == item.id
                )
            ).first()

            status_csv = get_val(row, 'STATUS') or "Pendente"
            
            if not link:
                link = DiretivaItemAeronave(
                    aeronave_id=aeronave.id,
                    diretiva_item_id=item.id,
                    status=status_csv,
                    ordem_aplicada=ordem_ref,
                    observacao=get_val(row, 'OBSERVAÇÕES') or get_val(row, 'PJ'),
                    origem_status="csv",
                    ultima_referencia_snapshot=snapshot_ts
                )
                link.tendencia = 3
            else:
                link.status = status_csv
                link.ordem_aplicada = ordem_ref
                link.observacao = get_val(row, 'OBSERVAÇÕES') or get_val(row, 'PJ')
                link.ultima_referencia_snapshot = snapshot_ts
                link.origem_status = "csv"
                link.concluida_automaticamente = False # Reset se reapareceu no CSV
            
            session.add(link)
            session.flush()
            link.calculate_gut()
            links_processados_ids.append(link.id)
            processed_count += 1

        # 5. Snapshot Logic: Auto-concluir itens que não vieram no CSV para estas aeronaves
        for m in matriculas_no_csv:
            aero = aero_cache.get(m)
            if not aero: continue
            
            # Localiza links desta aeronave que NÃO foram processados neste lote e NÃO estão concluídos
            ausentes = session.exec(
                select(DiretivaItemAeronave).where(
                    DiretivaItemAeronave.aeronave_id == aero.id,
                    DiretivaItemAeronave.id.not_in(links_processados_ids),
                    DiretivaItemAeronave.status != "Concluída"
                )
            ).all()
            
            for link_ausente in ausentes:
                link_ausente.status = "Concluída"
                link_ausente.concluida_automaticamente = True
                link_ausente.observacao = f"[AUTO] Concluída via snapshot em {snapshot_ts}. Motivo: Item ausente no CSV."
                session.add(link_ausente)

        session.commit()
    
    return processed_count
