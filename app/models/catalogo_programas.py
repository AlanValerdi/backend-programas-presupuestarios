from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class CatalogoProgramas(Base):
    __tablename__ = "catalogo_programas"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False) # clave del programa presupuestal
    programa = Column(String, nullable=False) # TBD: Los programas deberian venir de un catalogo, pero por ahora lo dejamos como string

    # Llaves foraneas
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id"), nullable=False)
    unidad_administrativa_id = Column(Integer, ForeignKey("catalogo_unidades_administrativas.id"), nullable=False)
    
    # Relaciones
    ejercicio = relationship("Ejercicio", back_populates="programas")
    unidad_administrativa = relationship("CatalogoUnidadesAdministrativas", back_populates="programas")
    componentes = relationship("Componentes", back_populates="programa")

    # metricas
    activo = Column(Boolean, default=True)
    estado_flujo = Column(String, nullable=False, default="configuracion", server_default="configuracion")
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())