import pandas as pd
from sqlmodel import Session, select
from app.models import DiretivaTecnica, DiretivaItem, DiretivaItemAeronave, Aeronave, Snapshot
from app.database import engine
from io import StringIO
from datetime import datetime, timezone
from typing import Optional
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

def process_csv(csv_content: str, filename: Optional[str] = None):
    df = pd.read_csv(StringIO(csv_content), sep=';', skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    
    # Gerar hash do conteúdo para evitar reprocessamento idêntico se necessário (opcional)
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
    
    with Session(engine) as session:
        # Cache de Aeronaves e Mestres para performance (usando codigo_simplificado como chave no cache)
        aero_cache = {a.matricula: a for a in session.exec(select(Aeronave)).all()}
        dt_cache = {d.codigo_simplificado: d for d in session.exec(select(DiretivaTecnica)).all()}
        
        # Identificar aeronaves presentes no CSV
        matriculas_no_csv = df['MATR'].dropna().unique()
        
        # Criar snapshots para cada aeronave
        aero_snapshots = {}
        for m in matriculas_no_csv:
            aero = aero_cache.get(m)
            if not aero:
                # Se a aeronave não existe, precisamos criar agora para ter o ID para o Snapshot
                continue
            
            snap = Snapshot(
                aeronave_id=aero.id,
                data_hora=now_utc,
                nome_arquivo=filename,
                hash_conteudo=content_hash
            )
            session.add(snap)
            session.flush()
            aero_snapshots[aero.id] = snap

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
                
                # Criar snapshot para aeronave nova
                snap = Snapshot(
                    aeronave_id=aeronave.id,
                    data_hora=now_utc,
                    nome_arquivo=filename,
                    hash_conteudo=content_hash
                )
                session.add(snap)
                session.flush()
                aero_snapshots[aeronave.id] = snap
            elif aeronave.numero_serie != sn:
                aeronave.numero_serie = sn
                session.add(aeronave)

            raw_codigo_dt = get_val(row, 'DIRETIVA TÉCNICA')
            if not raw_codigo_dt: continue
            
            codigo_simplificado = sanitize_codigo(raw_codigo_dt)

            # 2. DiretivaTecnica Upsert (Mestre)
            dt = dt_cache.get(codigo_simplificado)
            dt_data = {
                "codigo_simplificado": codigo_simplificado,
                "codigo": raw_codigo_dt, # Rótulo original para exibição
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
                session.add(dt)
                session.flush()
                dt_cache[codigo_simplificado] = dt
            else:
                # Regra de Consolidação
                for key, value in dt_data.items():
                    if value:
                        setattr(dt, key, value)
                session.add(dt)

            # 3. DiretivaItem Upsert (Subordinado)
            fadt = get_val(row, 'FADT')
            tarefa = get_val(row, 'TAREFA')
            ordem_ref = get_val(row, 'ORDEM')
            chave = generate_chave_item(codigo_simplificado, fadt, tarefa, ordem_ref)
            
            # Busca item no banco
            item = session.exec(
                select(DiretivaItem).where(
                    DiretivaItem.diretiva_tecnica_id == dt.codigo_simplificado,
                    DiretivaItem.chave_item == chave
                )
            ).first()

            if not item:
                item = DiretivaItem(
                    diretiva_tecnica_id=dt.codigo_simplificado,
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
            snap = aero_snapshots.get(aeronave.id)
            
            if not link:
                link = DiretivaItemAeronave(
                    aeronave_id=aeronave.id,
                    diretiva_item_id=item.id,
                    snapshot_id=snap.id if snap else None,
                    status=status_csv,
                    ordem_aplicada=ordem_ref,
                    observacao=get_val(row, 'OBSERVAÇÕES') or get_val(row, 'PJ'),
                    origem_status="csv",
                    ultima_referencia_snapshot=now_utc.isoformat()
                )
                link.tendencia = 3
            else:
                link.status = status_csv
                link.snapshot_id = snap.id if snap else None
                link.ordem_aplicada = ordem_ref
                link.observacao = get_val(row, 'OBSERVAÇÕES') or get_val(row, 'PJ')
                link.ultima_referencia_snapshot = now_utc.isoformat()
                link.origem_status = "csv"
                link.concluida_automaticamente = False
            
            session.add(link)
            session.flush()
            link.calculate_gut()
            links_processados_ids.append(link.id)
            processed_count += 1

        # 5. Snapshot Logic: Auto-concluir itens que não vieram no CSV
        for m in matriculas_no_csv:
            aero = aero_cache.get(m)
            if not aero: continue
            
            ausentes = session.exec(
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
                session.add(link_ausente)

        session.commit()
    
    return processed_count
