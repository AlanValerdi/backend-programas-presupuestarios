"""add multi-tenant entidades and campos_extra

Revision ID: b7e8f9a0c1d2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-05 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7e8f9a0c1d2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entidades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_entidades_id"), "entidades", ["id"], unique=False)
    op.create_index(op.f("ix_entidades_slug"), "entidades", ["slug"], unique=True)

    op.create_table(
        "entity_field_contracts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["entidad_id"], ["entidades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entidad_id", "entity_type", name="uq_entity_field_contracts_entidad_type"),
    )
    op.create_index(op.f("ix_entity_field_contracts_id"), "entity_field_contracts", ["id"], unique=False)

    # Seed Huachinango for backfill
    op.execute(
        """
        INSERT INTO entidades (slug, nombre, activo)
        VALUES ('huachinango', 'Huachinango', true)
        """
    )

    # --- ejercicios ---
    op.add_column("ejercicios", sa.Column("entidad_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE ejercicios
        SET entidad_id = (SELECT id FROM entidades WHERE slug = 'huachinango' LIMIT 1)
        """
    )
    op.alter_column("ejercicios", "entidad_id", nullable=False)
    op.create_foreign_key("fk_ejercicios_entidad_id", "ejercicios", "entidades", ["entidad_id"], ["id"])
    op.create_index(op.f("ix_ejercicios_entidad_id"), "ejercicios", ["entidad_id"], unique=False)
    op.drop_constraint("ejercicios_anio_key", "ejercicios", type_="unique")
    op.create_unique_constraint("uq_ejercicios_entidad_anio", "ejercicios", ["entidad_id", "anio"])

    # --- usuarios ---
    op.add_column("usuarios", sa.Column("entidad_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE usuarios
        SET entidad_id = (SELECT id FROM entidades WHERE slug = 'huachinango' LIMIT 1)
        """
    )
    op.alter_column("usuarios", "entidad_id", nullable=False)
    op.create_foreign_key("fk_usuarios_entidad_id", "usuarios", "entidades", ["entidad_id"], ["id"])
    op.create_index(op.f("ix_usuarios_entidad_id"), "usuarios", ["entidad_id"], unique=False)
    op.drop_constraint("usuarios_username_key", "usuarios", type_="unique")
    op.drop_constraint("usuarios_email_key", "usuarios", type_="unique")
    op.create_unique_constraint("uq_usuarios_entidad_username", "usuarios", ["entidad_id", "username"])
    op.create_unique_constraint("uq_usuarios_entidad_email", "usuarios", ["entidad_id", "email"])

    # --- catalogo_unidades_administrativas ---
    op.add_column("catalogo_unidades_administrativas", sa.Column("entidad_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE catalogo_unidades_administrativas
        SET entidad_id = (SELECT id FROM entidades WHERE slug = 'huachinango' LIMIT 1)
        """
    )
    op.alter_column("catalogo_unidades_administrativas", "entidad_id", nullable=False)
    op.create_foreign_key(
        "fk_unidades_entidad_id",
        "catalogo_unidades_administrativas",
        "entidades",
        ["entidad_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_catalogo_unidades_administrativas_entidad_id"),
        "catalogo_unidades_administrativas",
        ["entidad_id"],
        unique=False,
    )

    # --- catalogo_programas ---
    op.add_column("catalogo_programas", sa.Column("entidad_id", sa.Integer(), nullable=True))
    op.add_column(
        "catalogo_programas",
        sa.Column("campos_extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.execute(
        """
        UPDATE catalogo_programas
        SET entidad_id = (SELECT id FROM entidades WHERE slug = 'huachinango' LIMIT 1)
        """
    )
    op.alter_column("catalogo_programas", "entidad_id", nullable=False)
    op.create_foreign_key("fk_programas_entidad_id", "catalogo_programas", "entidades", ["entidad_id"], ["id"])
    op.create_index(op.f("ix_catalogo_programas_entidad_id"), "catalogo_programas", ["entidad_id"], unique=False)

    # --- catalogo_fuentes_financiamiento ---
    op.add_column("catalogo_fuentes_financiamiento", sa.Column("entidad_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE catalogo_fuentes_financiamiento
        SET entidad_id = (SELECT id FROM entidades WHERE slug = 'huachinango' LIMIT 1)
        """
    )
    op.alter_column("catalogo_fuentes_financiamiento", "entidad_id", nullable=False)
    op.create_foreign_key(
        "fk_fuentes_entidad_id",
        "catalogo_fuentes_financiamiento",
        "entidades",
        ["entidad_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_catalogo_fuentes_financiamiento_entidad_id"),
        "catalogo_fuentes_financiamiento",
        ["entidad_id"],
        unique=False,
    )

    # --- catalogo_pmd ---
    op.add_column("catalogo_pmd", sa.Column("entidad_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE catalogo_pmd
        SET entidad_id = (SELECT id FROM entidades WHERE slug = 'huachinango' LIMIT 1)
        """
    )
    op.alter_column("catalogo_pmd", "entidad_id", nullable=False)
    op.create_foreign_key("fk_pmd_entidad_id", "catalogo_pmd", "entidades", ["entidad_id"], ["id"])
    op.create_index(op.f("ix_catalogo_pmd_entidad_id"), "catalogo_pmd", ["entidad_id"], unique=False)

    # --- actividades campos_extra ---
    op.add_column(
        "actividades",
        sa.Column("campos_extra", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )


def downgrade() -> None:
    op.drop_column("actividades", "campos_extra")

    op.drop_index(op.f("ix_catalogo_pmd_entidad_id"), table_name="catalogo_pmd")
    op.drop_constraint("fk_pmd_entidad_id", "catalogo_pmd", type_="foreignkey")
    op.drop_column("catalogo_pmd", "entidad_id")

    op.drop_index(op.f("ix_catalogo_fuentes_financiamiento_entidad_id"), table_name="catalogo_fuentes_financiamiento")
    op.drop_constraint("fk_fuentes_entidad_id", "catalogo_fuentes_financiamiento", type_="foreignkey")
    op.drop_column("catalogo_fuentes_financiamiento", "entidad_id")

    op.drop_index(op.f("ix_catalogo_programas_entidad_id"), table_name="catalogo_programas")
    op.drop_constraint("fk_programas_entidad_id", "catalogo_programas", type_="foreignkey")
    op.drop_column("catalogo_programas", "campos_extra")
    op.drop_column("catalogo_programas", "entidad_id")

    op.drop_index(op.f("ix_catalogo_unidades_administrativas_entidad_id"), table_name="catalogo_unidades_administrativas")
    op.drop_constraint("fk_unidades_entidad_id", "catalogo_unidades_administrativas", type_="foreignkey")
    op.drop_column("catalogo_unidades_administrativas", "entidad_id")

    op.drop_constraint("uq_usuarios_entidad_email", "usuarios", type_="unique")
    op.drop_constraint("uq_usuarios_entidad_username", "usuarios", type_="unique")
    op.drop_index(op.f("ix_usuarios_entidad_id"), table_name="usuarios")
    op.drop_constraint("fk_usuarios_entidad_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "entidad_id")
    op.create_unique_constraint("usuarios_email_key", "usuarios", ["email"])
    op.create_unique_constraint("usuarios_username_key", "usuarios", ["username"])

    op.drop_constraint("uq_ejercicios_entidad_anio", "ejercicios", type_="unique")
    op.drop_index(op.f("ix_ejercicios_entidad_id"), table_name="ejercicios")
    op.drop_constraint("fk_ejercicios_entidad_id", "ejercicios", type_="foreignkey")
    op.drop_column("ejercicios", "entidad_id")
    op.create_unique_constraint("ejercicios_anio_key", "ejercicios", ["anio"])

    op.drop_index(op.f("ix_entity_field_contracts_id"), table_name="entity_field_contracts")
    op.drop_table("entity_field_contracts")
    op.drop_index(op.f("ix_entidades_slug"), table_name="entidades")
    op.drop_index(op.f("ix_entidades_id"), table_name="entidades")
    op.drop_table("entidades")
