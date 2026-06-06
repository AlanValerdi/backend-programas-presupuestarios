from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Componentes(Base):
    __tablename__ = "componentes"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False) # clave del componente
    descripcion = Column(String, nullable=False) # descripcion del componente

    # Llaves foraneas
    programa_id = Column(Integer, ForeignKey("catalogo_programas.id"), nullable=False)

    # Relaciones
    programa = relationship("CatalogoProgramas", back_populates="componentes")
    actividades = relationship("Actividades", back_populates="componente")

    # metricas
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())