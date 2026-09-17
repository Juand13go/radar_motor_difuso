"""declarar las fechas con zona horaria

Revision ID: c8d3e5f10a27
Revises: b4f1c72a9e30
Create Date: 2026-09-16 20:21:44.903512

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'c8d3e5f10a27'
down_revision: Union[str, Sequence[str], None] = 'b4f1c72a9e30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # El contenedor corre en UTC, asi que lo ya guardado es UTC sin etiquetar: el AT TIME ZONE lo declara sin mover el instante
    op.alter_column('conversaciones', 'conv_actualizado_en',
    type_=sa.DateTime(timezone=True),
    existing_type=sa.DateTime(),
    existing_nullable=False,
    postgresql_using="conv_actualizado_en AT TIME ZONE 'UTC'")
    op.alter_column('mensajes', 'creado_en',
    type_=sa.DateTime(timezone=True),
    existing_type=sa.DateTime(),
    existing_nullable=False,
    postgresql_using="creado_en AT TIME ZONE 'UTC'")
    op.alter_column('leads', 'lead_creado_en',
    type_=sa.DateTime(timezone=True),
    existing_type=sa.DateTime(),
    existing_nullable=False,
    postgresql_using="lead_creado_en AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('leads', 'lead_creado_en',
    type_=sa.DateTime(),
    existing_type=sa.DateTime(timezone=True),
    existing_nullable=False,
    postgresql_using="lead_creado_en AT TIME ZONE 'UTC'")
    op.alter_column('mensajes', 'creado_en',
    type_=sa.DateTime(),
    existing_type=sa.DateTime(timezone=True),
    existing_nullable=False,
    postgresql_using="creado_en AT TIME ZONE 'UTC'")
    op.alter_column('conversaciones', 'conv_actualizado_en',
    type_=sa.DateTime(),
    existing_type=sa.DateTime(timezone=True),
    existing_nullable=False,
    postgresql_using="conv_actualizado_en AT TIME ZONE 'UTC'")
