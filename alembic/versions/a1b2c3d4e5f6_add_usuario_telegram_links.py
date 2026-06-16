"""add_usuario_telegram_links

Revision ID: a1b2c3d4e5f6
Revises: c43b685c3a64
Create Date: 2026-06-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c43b685c3a64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuario_telegram_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("telegram_chat_id", sa.String(length=50), nullable=True),
        sa.Column("telegram_user_id", sa.String(length=50), nullable=True),
        sa.Column("telegram_username", sa.String(length=100), nullable=True),
        sa.Column("telegram_phone_number", sa.String(length=20), nullable=True),
        sa.Column("link_token_hash", sa.String(length=64), nullable=True),
        sa.Column("link_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
        sa.UniqueConstraint("telegram_chat_id"),
    )
    op.create_index(
        op.f("ix_usuario_telegram_links_id"),
        "usuario_telegram_links",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_usuario_telegram_links_link_token_hash"),
        "usuario_telegram_links",
        ["link_token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_usuario_telegram_links_link_token_hash"),
        table_name="usuario_telegram_links",
    )
    op.drop_index(op.f("ix_usuario_telegram_links_id"), table_name="usuario_telegram_links")
    op.drop_table("usuario_telegram_links")
