from sqlalchemy import Table, Column, Integer, DateTime, Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RolUsuario:
    ADMINISTRADOR = "administrador"
    PROGRAMACION_PRESUPUESTAL = "programacion-presupuestal"
    PLANEACION = "planeacion"
    EJECUTOR = "ejecutores"


# Table to associate users to multiple administrative units (Many-to-Many)
usuario_unidad_asociacion = Table(
    "usuario_unidad_asociacion",
    Base.metadata,
    Column(
        "usuario_id",
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "unidad_administrativa_id",
        Integer,
        ForeignKey("catalogo_unidades_administrativas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("entidad_id", "username", name="uq_usuarios_entidad_username"),
        UniqueConstraint("entidad_id", "email", name="uq_usuarios_entidad_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)

    rol = Column(String(50), nullable=False, default=RolUsuario.EJECUTOR)

    entidad_id = Column(Integer, ForeignKey("entidades.id"), nullable=False, index=True)

    unidad_administrativa_id = Column(
        Integer, ForeignKey("catalogo_unidades_administrativas.id"), nullable=True
    )

    activo = Column(Boolean, default=True)
    mostrar_montos = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    entidad = relationship("Entidad")
    unidad_administrativa = relationship(
        "CatalogoUnidadesAdministrativas", foreign_keys=[unidad_administrativa_id]
    )
    unidades_administrativas = relationship(
        "CatalogoUnidadesAdministrativas",
        secondary=usuario_unidad_asociacion,
        backref="usuarios"
    )
