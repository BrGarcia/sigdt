import pytest
from sqlalchemy import inspect
from app.database import engine
from sqlmodel import Session, select
import os
import subprocess

def test_migration_produces_correct_schema():
    """
    Testa se rodar as migrações em um banco novo produz o schema esperado.
    """
    test_db = "migration_check.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Rodar upgrade head usando o banco temporário
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{test_db}"
    
    result = subprocess.run(
        ["python3", "-m", "alembic", "upgrade", "head"],
        env=env,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Alembic upgrade failed: {result.stderr}"
    
    # Inspecionar o banco resultante
    from sqlalchemy import create_engine
    test_engine = create_engine(f"sqlite:///{test_db}")
    inspector = inspect(test_engine)
    
    tables = inspector.get_table_names()
    assert "diretiva_tecnica" in tables
    assert "diretiva_item" in tables
    assert "diretiva_item_aeronave" in tables
    assert "aeronave" in tables
    assert "snapshot" in tables
    assert "user" in tables
    
    # Verificar PK de diretiva_tecnica
    pk_dt = inspector.get_pk_constraint("diretiva_tecnica")
    assert pk_dt["constrained_columns"] == ["codigo_simplificado"]
    
    # Verificar colunas de diretiva_tecnica
    columns_dt = {c["name"]: c for c in inspector.get_columns("diretiva_tecnica")}
    assert "id" not in columns_dt
    assert "codigo_simplificado" in columns_dt
    
    # Verificar FK de diretiva_item
    fks_item = inspector.get_foreign_keys("diretiva_item")
    dt_fk = next(fk for fk in fks_item if fk["referred_table"] == "diretiva_tecnica")
    assert dt_fk["referred_columns"] == ["codigo_simplificado"]
    assert dt_fk["constrained_columns"] == ["diretiva_tecnica_id"]

    if os.path.exists(test_db):
        os.remove(test_db)
