from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class CapturaPeriodos(Base):
    __tablename__ = "captura_periodos"

    id = Column(Integer, primary_key=True, index=True)
    # TODO: agregar columna para el año fiscal/ejercicio
    mes = Column(Integer, nullable=False) # 1-12 para representar los meses del año

    fecha_inicio = Column(DateTime, nullable=False) # inicio del periodo de captura
    fecha_fin = Column(DateTime, nullable=False) # fin del periodo de captura
    activo = Column(Boolean, default=True)

    # metricas simples para auditoría y seguimiento
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # programa_id = Column(Integer, ForeignKey("programas.id"), nullable=False)
    # programa = relationship("Programas", back_populates="periodos_captura")