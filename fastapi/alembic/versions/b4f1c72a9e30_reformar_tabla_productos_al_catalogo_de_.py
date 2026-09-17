"""reformar tabla productos al catalogo de tornalba

Revision ID: b4f1c72a9e30
Revises: 36da448fd5c4
Create Date: 2026-09-16 20:14:02.118366

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'b4f1c72a9e30'
down_revision: Union[str, Sequence[str], None] = '36da448fd5c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # El catalogo anterior es de otro dominio (Rambler), asi que se descarta en vez de migrarse
    op.drop_table('productos')
    op.create_table('productos',
    sa.Column('id_producto', sa.Integer(), nullable=False),
    sa.Column('referencia', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('nombre_producto', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('categoria', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('unidad', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('precio_unitario', sa.Numeric(), nullable=False),
    sa.Column('existencias', sa.Integer(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id_producto')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('productos')
    op.create_table('productos',
    sa.Column('id_woocommerce', sa.Integer(), nullable=False),
    sa.Column('nombre_producto', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('precio_regular', sa.Numeric(), nullable=False),
    sa.Column('precio_venta', sa.Numeric(), nullable=False),
    sa.Column('categoria', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id_woocommerce')
    )
