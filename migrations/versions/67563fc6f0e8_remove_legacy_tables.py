"""remove legacy tables

Revision ID: 67563fc6f0e8
Revises: 1d3fc7e34187
Create Date: 2026-03-31 18:54:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '67563fc6f0e8'
down_revision: Union[str, Sequence[str], None] = '1d3fc7e34187'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_table('diretivaaeronave')
    op.drop_table('diretiva')

def downgrade() -> None:
    # This is a one-way migration for cleanup
    pass
