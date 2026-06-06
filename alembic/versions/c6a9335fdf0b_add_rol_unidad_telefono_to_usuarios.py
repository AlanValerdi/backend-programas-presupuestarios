"""add_rol_unidad_telefono_to_usuarios

Revision ID: c6a9335fdf0b
Revises: 5e4ef7869196
Create Date: 2026-06-06 12:16:37.525100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision: str = 'c6a9335fdf0b'
down_revision: Union[str, Sequence[str], None] = '5e4ef7869196'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    table_exists = 'usuarios' in inspector.get_table_names()

    if not table_exists:
        op.create_table('usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('rol', sa.String(length=50), nullable=False),
        sa.Column('unidad_administrativa_id', sa.Integer(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['unidad_administrativa_id'], ['catalogo_unidades_administrativas.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
        )
        op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)
    else:
        columns_in_table = [col['name'] for col in inspector.get_columns('usuarios')]
        if 'telefono' not in columns_in_table:
            op.add_column('usuarios', sa.Column('telefono', sa.String(length=20), nullable=True))
        if 'rol' not in columns_in_table:
            op.add_column('usuarios', sa.Column('rol', sa.String(length=50), nullable=False, server_default='ejecutores'))
        if 'unidad_administrativa_id' not in columns_in_table:
            op.add_column('usuarios', sa.Column('unidad_administrativa_id', sa.Integer(), nullable=True))
        if 'ix_usuarios_id' not in [idx['name'] for idx in inspector.get_indexes('usuarios')]:
            op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    table_exists = 'usuarios' in inspector.get_table_names()

    op.drop_index(op.f('ix_usuarios_id'), table_name='usuarios')
    if table_exists:
        op.drop_column('usuarios', 'unidad_administrativa_id')
        op.drop_column('usuarios', 'rol')
        op.drop_column('usuarios', 'telefono')
