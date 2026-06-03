from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

# Este modelo representa al EJECUTOR a nivel matriz programatica y al catalogo de UNIDADES ADMINISTRATIVAS.
class CatalogoUnidadesAdministrativas(Base):
    __tablename__ = "catalogo_unidades_administrativas"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False) # clave o NUMERO de la unidad administrativa
    plazas = Column(Integer, nullable=True) 
    nombre = Column(String, nullable=False) # nombre de la unidad administrativa
    activo = Column(Boolean, default=True)

    # metricas
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    techos_financieros = relationship("TechoFinanciero", back_populates="unidad_administrativa")
    programas = relationship("CatalogoProgramas", back_populates="unidad_administrativa")

     
