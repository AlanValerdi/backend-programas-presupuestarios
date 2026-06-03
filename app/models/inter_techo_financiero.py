from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

# Este modelo representa la tabla intermedia entre las unidades administrativas y las fuentes de financiamiento, 
# donde se asignan los techos financieros para cada combinación de unidad administrativa y fuente de financiamiento
# en un ejercicio fiscal determinado.
# TODO: Integrar el ejercicio fiscal (año) en este modelo, para poder tener techos financieros específicos por año.

class TechoFinanciero(Base):
    __tablename__ = "techos_financieros"

    id = Column(Integer, primary_key=True, index=True)
    # ejercicio_id = Column(Integer, ForeignKey("ejercicios.id"), nullable=False)
    unidad_administrativa_id = Column(Integer, ForeignKey("catalogo_unidades_administrativas.id"), nullable=False)
    fuente_financiamiento_id = Column(Integer, ForeignKey("catalogo_fuentes_financiamiento.id"), nullable=False)
    
    # Numeric(15, 2) significa hasta 15 dígitos en total, 2 de ellos decimales.
    monto = Column(Numeric(15, 2), default=0.00, nullable=False)

    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    unidad_administrativa = relationship("CatalogoUnidadesAdministrativas", back_populates="techos_financieros")
    fuente_financiamiento = relationship("CatalogoFuentesFinanciamiento", back_populates="techos_financieros")
    # ejercicio = relationship("Ejercicio", back_populates="techos_financieros") # Asumiendo que agregas esto en Ejercicio