import pandas as pd
from sqlmodel import Session, select
from app.models import DiretivaTecnica, DiretivaItem, DiretivaItemAeronave, Aeronave, Snapshot
from app.database import engine
from io import StringIO
from datetime import datetime, timezone
from typing import Optional, List, Dict
import hashlib
import re

def sanitize_formula(value):
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

def sanitize_codigo(codigo: str) -> str:
    """Remove todos os espaços e símbolos, deixando apenas letras e números."""
    if not codigo: return ""
    return re.sub(r'[^A-Z0-9]', '', str(codigo).upper())

def generate_chave_item(codigo_simplificado: str, fadt: Optional[str], tarefa: Optional[str], ordem: Optional[str]) -> str:
    """Gera uma chave determinística para deduplicação do item usando o código simplificado."""
    c = str(codigo_simplificado or "").strip().upper()
    f = str(fadt or "").strip().upper()
    t = str(tarefa or "").strip().upper()
    o = str(ordem or "").strip().upper()
    return f"{c}|{f}|{t}|{o}"

def process_csv(csv_content: str, filename: Optional[str] = None, session: Optional[Session] = None):
    # OTIMIZAÇÃO LOTE 4: Processamento em Chunks (Lotes) para economizar RAM
    CHUNK_SIZE = 500
    
    # Gerar hash do conteúdo para o snapshot
    content_hash = hashlib.sha256(csv_content.encode('utf-8')).hexdigest()
    
    def get_val(row, col_name):
        val = row.get(col_name)
        if isinstance(val, pd.Series):
            val = val.iloc[0]
        if pd.isna(val) or str(val).lower() == 'nan' or str(val).strip() == '':
            return None
        return sanitize_formula(str(val).strip())

    now_utc = datetime.now(timezone.utc)
    processed_count = 0
    
    # Use provided session or create a new one
    internal_session = session if session else Session(engine)
    
    # Estado compartilhado entre chunks para manter integridade do snapshot
    matriculas_no_csv = set()
    links_processados_ids = []
    
    try:
        # Caches globais (atualizados ao longo dos chunks)
        aero_cache = {a.matricula: a for a in internal_session.exec(select(Aeronave)).all()}
        dt_cache = {d.codigo_simplificado: d for d in internal_session.exec(select(DiretivaTecnica)).all()}
        item_cache = {
            (i.diretiva_tecnica_id, i.chave_item): i 
            for i in internal_session.exec(select(DiretivaItem)).all()
        }
        link_cache = {
            (l.aeronave_id, l.diretiva_item_id): l 
            for l in internal_session.exec(select(DiretivaItemAeronave)).all()
        }
        aero_snapshots = {}

        # Iterar sobre o CSV em pedaços
        for chunk in pd.read_csv(StringIO(csv_content), sep=';', skipinitialspace=True, chunksize=CHUNK_SIZE):
            chunk.columns = [c.strip() for c in chunk.columns]
            
            # Identificar aeronaves presentes neste chunk
            chunk_matriculas = chunk['MATR'].dropna().unique()
            for m in chunk_matriculas:
                matriculas_no_csv.add(m)
                
                # Garantir snapshot para cada aeronave (uma única vez por aeronave no arquivo inteiro)
                aero = aero_cache.get(m)
                if aero and aero.id not in aero_snapshots:
                    snap = Snapshot(
                        aeronave_id=aero.id,
                        data_hora=now_utc,
                        nome_arquivo=filename,
                        hash_conteudo=content_hash
                    )
                    internal_session.add(snap)
                    internal_session.flush()
                    aero_snapshots[aero.id] = snap

            for i, row in chunk.iterrows():
                matricula = get_val(row, 'MATR')
                sn = get_val(row, 'SN')
                if not matricula or not sn: continue

                # 1. Aeronave Upsert
                aeronave = aero_cache.get(matricula)
                if not aeronave:
                    aeronave = Aeronave(matricula=matricula, numero_serie=sn)
                    internal_session.add(aeronave)
                    internal_session.flush()
                    aero_cache[matricula] = aeronave
                    
                    # Snapshot para aeronave nova
                    snap = Snapshot(
                        aeronave_id=aeronave.id,
                        data_hora=now_utc,
                        nome_arquivo=filename,
                        hash_conteudo=content_hash
                    )
                    internal_session.add(snap)
                    internal_session.flush()
                    aero_snapshots[aeronave.id] = snap
                elif aeronave.numero_serie != sn:
                    aeronave.numero_serie = sn
                    internal_session.add(aeronave)

                raw_codigo_dt = get_val(row, 'DIRETIVA TÉCNICA')
                if not raw_codigo_dt: continue
                
                codigo_simplificado = sanitize_codigo(raw_codigo_dt)

                # 2. DiretivaTecnica Upsert (Mestre)
                dt = dt_cache.get(codigo_simplificado)
                dt_data = {
                    "codigo_simplificado": codigo_simplificado,
                    "codigo": raw_codigo_dt,
                    "objetivo": get_val(row, 'OBJETIVO'),
                    "classe": get_val(row, 'CLA'),
                    "categoria": get_val(row, 'CAT'),
                    "tipo": get_val(row, 'TIPO INCORPORAÇÃO'),
                    "natureza": get_val(row, 'NAT'),
                    "especialidade": get_val(row, 'ESPECIALIDADE'),
                    "updated_at": now_utc
                }
                if not dt:
                    dt = DiretivaTecnica(**dt_data)
                    internal_session.add(dt)
                    internal_session.flush()
                    dt_cache[codigo_simplificado] = dt
                else:
                    for key, value in dt_data.items():
                        if value: setattr(dt, key, value)
                    internal_session.add(dt)

                # 3. DiretivaItem Upsert
                fadt = get_val(row, 'FADT')
                tarefa = get_val(row, 'TAREFA')
                ordem_ref = get_val(row, 'ORDEM')
                chave_item = generate_chave_item(codigo_simplificado, fadt, tarefa, ordem_ref)
                
                item = item_cache.get((codigo_simplificado, chave_item))
                if not item:
                    item = DiretivaItem(
                        diretiva_tecnica_id=codigo_simplificado,
                        fadt=fadt, tarefa=tarefa, ordem_referencia=ordem_ref,
                        chave_item=chave_item, descricao_item=get_val(row, 'OBJETIVO'),
                        updated_at=now_utc
                    )
                    internal_session.add(item)
                    internal_session.flush()
                    item_cache[(codigo_simplificado, chave_item)] = item
                else:
                    desc = get_val(row, 'OBJETIVO')
                    if desc: item.descricao_item = desc
                    item.updated_at = now_utc
                    internal_session.add(item)

                # 4. Link Aeronave-Item Upsert
                link = link_cache.get((aeronave.id, item.id))
                status = get_val(row, 'STATUS') or "Pendente"
                
                if not link:
                    link = DiretivaItemAeronave(
                        aeronave_id=aeronave.id,
                        diretiva_item_id=item.id,
                        snapshot_id=aero_snapshots[aeronave.id].id if aeronave.id in aero_snapshots else None,
                        status=status,
                        data_status=now_utc,
                        ordem_aplicada=get_val(row, 'ORDEM'),
                        observacao=get_val(row, 'OBSERVAÇÕES'),
                        origem_status='csv',
                        updated_at=now_utc
                    )
                    internal_session.add(link)
                    internal_session.flush()
                    link_cache[(aeronave.id, item.id)] = link
                else:
                    link.status = status
                    link.ordem_aplicada = get_val(row, 'ORDEM')
                    link.observacao = get_val(row, 'OBSERVAÇÕES')
                    link.snapshot_id = aero_snapshots[aeronave.id].id if aeronave.id in aero_snapshots else link.snapshot_id
                    link.updated_at = now_utc
                    link.concluida_automaticamente = False
                    internal_session.add(link)
                
                link.calculate_gut()
                links_processados_ids.append(link.id)
                processed_count += 1
            
            # Flush a cada chunk para evitar acúmulo excessivo na sessão SQLAlchemy
            internal_session.flush()

        # 5. Final Snapshot Logic (Auto-conclusão)
        for m in matriculas_no_csv:
            aero = aero_cache.get(m)
            if not aero: continue
            
            ausentes = internal_session.exec(
                select(DiretivaItemAeronave).where(
                    DiretivaItemAeronave.aeronave_id == aero.id,
                    DiretivaItemAeronave.id.not_in(links_processados_ids),
                    DiretivaItemAeronave.status != "Concluída",
                    DiretivaItemAeronave.status != "Não aplicável"
                )
            ).all()
            
            for link_ausente in ausentes:
                link_ausente.status = "Concluída"
                link_ausente.concluida_automaticamente = True
                link_ausente.observacao = f"[AUTO] Concluída via snapshot em {now_utc.isoformat()}. Motivo: Item ausente no CSV ({filename})."
                internal_session.add(link_ausente)

        internal_session.commit()
    finally:
        if not session:
            internal_session.close()
    
    return processed_count
