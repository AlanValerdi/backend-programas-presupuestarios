from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RolUsuario:
    PROGRAMACION_PRESUPUESTAL = "programacion-presupuestal"
    PLANEACION = "planeacion"
    EJECUTOR = "ejecutores"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)

    rol = Column(String(50), nullable=False, default=RolUsuario.EJECUTOR)

    unidad_administrativa_id = Column(
        Integer, ForeignKey("catalogo_unidades_administrativas.id"), nullable=True
    )

    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    programaciones = relationship("ProgramacionMeta", back_populates="usuario")
    unidad_administrativa = relationship(
        "CatalogoUnidadesAdministrativas", foreign_keys=[unidad_administrativa_id]
    )