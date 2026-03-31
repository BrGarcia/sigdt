"""data: migrate legacy data to new model

Revision ID: 1d3fc7e34187
Revises: e6ca8f306a0d
Create Date: 2026-03-30 15:18:47.160437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1d3fc7e34187'
down_revision: Union[str, Sequence[str], None] = 'e6ca8f306a0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from datetime import datetime, timezone

def upgrade() -> None:
    # Use direct SQL via op.execute for data migration
    connection = op.get_bind()
    
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Migrate Diretiva -> DiretivaTecnica (Deduplicating by codigo_diretiva)
    # We pick the one with the longest 'objetivo' as the most 'complete' record for metadata
    diretivas_master = connection.execute(sa.text("""
        SELECT codigo_diretiva, objetivo, classe, categoria, tipo, natureza, especialidade
        FROM diretiva
        ORDER BY LENGTH(COALESCE(objetivo, '')) DESC
    """)).fetchall()
    
    processed_codigos = set()
    codigo_to_id = {}

    for d in diretivas_master:
        if d.codigo_diretiva in processed_codigos:
            continue
            
        connection.execute(sa.text("""
            INSERT INTO diretiva_tecnica (codigo, objetivo, classe, categoria, tipo, natureza, especialidade, ativa, created_at, updated_at)
            VALUES (:codigo, :objetivo, :classe, :categoria, :tipo, :natureza, :especialidade, 1, :now, :now)
        """), {
            "codigo": d.codigo_diretiva,
            "objetivo": d.objetivo,
            "classe": d.classe,
            "categoria": d.categoria,
            "tipo": d.tipo,
            "natureza": d.natureza,
            "especialidade": d.especialidade,
            "now": now
        })
        
        # Get the inserted ID
        new_id = connection.execute(sa.text("SELECT last_insert_rowid()")).scalar()
        codigo_to_id[d.codigo_diretiva] = new_id
        processed_codigos.add(d.codigo_diretiva)

    # 2. Migrate Diretiva -> DiretivaItem (Deduplicating by dt_id + chave_item)
    old_items = connection.execute(sa.text("""
        SELECT d.id as old_id, d.codigo_diretiva, d.fadt, d.ordem, d.objetivo
        FROM diretiva d
    """)).fetchall()
    
    processed_items = set() # (dt_id, chave_item)
    old_id_to_new_item_id = {}

    for d in old_items:
        dt_id = codigo_to_id.get(d.codigo_diretiva)
        if not dt_id: continue

        fadt_clean = str(d.fadt or "").strip().upper()
        ordem_clean = str(d.ordem or "").strip().upper()
        chave_item = f"{d.codigo_diretiva}|{fadt_clean}||{ordem_clean}"
        
        item_key = (dt_id, chave_item)
        
        if item_key not in processed_items:
            connection.execute(sa.text("""
                INSERT INTO diretiva_item (diretiva_tecnica_id, fadt, ordem_referencia, chave_item, descricao_item, ativo, created_at, updated_at)
                VALUES (:dt_id, :fadt, :ordem, :chave, :desc, 1, :now, :now)
            """), {
                "dt_id": dt_id,
                "fadt": d.fadt,
                "ordem": d.ordem,
                "chave": chave_item,
                "desc": d.objetivo,
                "now": now
            })
            new_item_id = connection.execute(sa.text("SELECT last_insert_rowid()")).scalar()
            processed_items.add(item_key)
            old_id_to_new_item_id[d.old_id] = new_item_id
        else:
            # If item already exists, find its ID to map links correctly
            existing_id = connection.execute(sa.text("SELECT id FROM diretiva_item WHERE diretiva_tecnica_id = :dt_id AND chave_item = :chave"), 
                                          {"dt_id": dt_id, "chave": chave_item}).scalar()
            old_id_to_new_item_id[d.old_id] = existing_id

    # 3. Migrate DiretivaAeronave -> DiretivaItemAeronave
    # Deduplicating (aeronave_id, item_id) - picking the most recent data_status link if multiple exist
    old_links = connection.execute(sa.text("""
        SELECT da.aeronave_id, da.diretiva_id, da.status, da.data_aplicacao, da.data_status, 
               da.ordem_aplicada, da.observacao, da.pdf_path, da.tendencia, da.gut
        FROM diretivaaeronave da
        ORDER BY da.data_status DESC
    """)).fetchall()
    
    processed_links = set() # (aeronave_id, item_id)
    
    for l in old_links:
        item_id = old_id_to_new_item_id.get(l.diretiva_id)
        if not item_id: continue
        
        link_key = (l.aeronave_id, item_id)
        if link_key in processed_links:
            continue

        connection.execute(sa.text("""
            INSERT INTO diretiva_item_aeronave (aeronave_id, diretiva_item_id, status, data_aplicacao, data_status, 
                                               ordem_aplicada, observacao, pdf_path, tendencia, gut, 
                                               origem_status, concluida_automaticamente, created_at, updated_at)
            VALUES (:a_id, :i_id, :status, :d_app, :d_stat, :o_app, :obs, :pdf, :tend, :gut, 'csv', 0, :now, :now)
        """), {
            "a_id": l.aeronave_id,
            "i_id": item_id,
            "status": l.status,
            "d_app": l.data_aplicacao,
            "d_stat": l.data_status or now,
            "o_app": l.ordem_aplicada,
            "obs": l.observacao,
            "pdf": l.pdf_path,
            "tend": l.tendencia,
            "gut": l.gut,
            "now": now
        })
        processed_links.add(link_key)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM diretiva_item_aeronave")
    op.execute("DELETE FROM diretiva_item")
    op.execute("DELETE FROM diretiva_tecnica")
