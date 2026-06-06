from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Actividades(Base):
    __tablename__ = "actividades"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False) # clave de la actividad
    descripcion = Column(String, nullable=False) # descripcion de la actividad
    monto = Column(Numeric(15, 2), default=0.00, nullable=False) # monto asignado a la actividad
    meta = Column(Integer, nullable=False, comment="Meta total anual") # meta o resultado esperado de la actividad TOTAL

    # Llaves foraneas
    componente_id = Column(Integer, ForeignKey("componentes.id"), nullable=False)

    # Relaciones
    componente = relationship("Componentes", back_populates="actividades")
    lineas_pmd = relationship("CatalogoPMD", secondary="inter_actividades_pmd", back_populates="actividades")
    metas_mensuales = relationship("ProgramacionMeta", back_populates="actividad")

    # metricas
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())