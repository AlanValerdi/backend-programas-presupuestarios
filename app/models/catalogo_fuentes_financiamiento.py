from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class CatalogoFuentesFinanciamiento(Base):
    __tablename__ = "catalogo_fuentes_financiamiento"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False, comment="Ej. 5.02") # clave de la fuente de financiamiento
    descripcion = Column(String, nullable=False, comment= "Ej. FAISMUN") # nombre de la fuente de financiamiento

    # Relaciones
    techos_financieros = relationship("TechoFinanciero", back_populates="fuente_financiamiento")
    # ejecutor = relationship("Ejecutores", back_populates="fuente_financiamiento")

    # metricas
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())