"""data: migrate legacy data to new model (ROBUST VERSION)

Revision ID: 1d3fc7e34187
Revises: e6ca8f306a0d
Create Date: 2026-03-30 15:18:47.160437

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision: str = '1d3fc7e34187'
down_revision: Union[str, Sequence[str], None] = 'e6ca8f306a0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. MESTRE: Diretiva -> DiretivaTecnica
    # Consolidação: Agrupar por codigo_diretiva e pegar o registro "mais completo"
    # (critério: soma de campos não nulos)
    diretivas_raw = connection.execute(sa.text("""
        SELECT codigo_diretiva, objetivo, classe, categoria, tipo, natureza, especialidade
        FROM diretiva
    """)).fetchall()
    
    mestre_data = {} # codigo -> data_dict
    for d in diretivas_raw:
        codigo = d.codigo_diretiva
        if not codigo: continue
        
        # Calcular score de completude
        score = sum(1 for v in [d.objetivo, d.classe, d.categoria, d.tipo, d.natureza, d.especialidade] if v and str(v).strip())
        
        if codigo not in mestre_data or score > mestre_data[codigo]['score']:
            mestre_data[codigo] = {
                'objetivo': d.objetivo,
                'classe': d.classe,
                'categoria': d.categoria,
                'tipo': d.tipo,
                'natureza': d.natureza,
                'especialidade': d.especialidade,
                'score': score
            }
            
    codigo_to_id = {}
    for codigo, data in mestre_data.items():
        connection.execute(sa.text("""
            INSERT INTO diretiva_tecnica (codigo, objetivo, classe, categoria, tipo, natureza, especialidade, ativa, created_at, updated_at)
            VALUES (:codigo, :objetivo, :classe, :categoria, :tipo, :natureza, :especialidade, 1, :now, :now)
        """), {
            "codigo": codigo,
            "objetivo": data['objetivo'],
            "classe": data['classe'],
            "categoria": data['categoria'],
            "tipo": data['tipo'],
            "natureza": data['natureza'],
            "especialidade": data['especialidade'],
            "now": now
        })
        new_id = connection.execute(sa.text("SELECT last_insert_rowid()")).scalar()
        codigo_to_id[codigo] = new_id

    # 2. ITEM: Diretiva -> DiretivaItem (Deduplicação por dt_id + chave_item)
    # Precisamos mapear todos os IDs antigos de 'diretiva' para os novos IDs de 'diretiva_item'
    old_items = connection.execute(sa.text("""
        SELECT id as old_id, codigo_diretiva, fadt, ordem, objetivo
        FROM diretiva
    """)).fetchall()
    
    item_cache = {} # (dt_id, chave_item) -> new_item_id
    old_id_to_new_item_id = {}

    for d in old_items:
        dt_id = codigo_to_id.get(d.codigo_diretiva)
        if not dt_id: continue

        fadt_clean = str(d.fadt or "").strip().upper()
        ordem_clean = str(d.ordem or "").strip().upper()
        # Chave item: CODIGO|FADT|TAREFA|ORDEM (Tarefa é nula no legado)
        chave_item = f"{d.codigo_diretiva}|{fadt_clean}||{ordem_clean}"
        
        cache_key = (dt_id, chave_item)
        
        if cache_key not in item_cache:
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
            item_cache[cache_key] = new_item_id
            
        old_id_to_new_item_id[d.old_id] = item_cache[cache_key]

    # 3. VÍNCULOS: DiretivaAeronave -> DiretivaItemAeronave
    # Consolidação: Para (aeronave, item), pegar o status mais recente
    old_links = connection.execute(sa.text("""
        SELECT aeronave_id, diretiva_id, status, data_aplicacao, data_status, 
               ordem_aplicada, observacao, pdf_path, tendencia, gut
        FROM diretivaaeronave
        ORDER BY data_status DESC
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
    op.execute("DELETE FROM diretiva_item_aeronave")
    op.execute("DELETE FROM diretiva_item")
    op.execute("DELETE FROM diretiva_tecnica")
