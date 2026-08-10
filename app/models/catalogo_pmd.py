from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class CatalogoPMD(Base):
    __tablename__ = "catalogo_pmd"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False) # clave de la linea de acción
    entidad_id = Column(Integer, ForeignKey("entidades.id"), nullable=False, index=True)
    
    # Relaciones
    entidad = relationship("Entidad")
    actividades = relationship("Actividades", secondary="inter_actividades_pmd", back_populates="lineas_pmd")

    # metricas
    # activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
