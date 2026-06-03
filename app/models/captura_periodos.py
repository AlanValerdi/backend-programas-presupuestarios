from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class CapturaPeriodos(Base):
    __tablename__ = "captura_periodos"

    id = Column(Integer, primary_key=True, index=True)
    mes = Column(Integer, nullable=False) # 1-12 para representar los meses del año
    fecha_inicio_reporte = Column(DateTime, nullable=False, comment="Abre la subida de evidencia")
    fecha_fin_reporte = Column(DateTime, nullable=False, comment="Cierra la subida de evidencia")
    activo = Column(Boolean, default=True)

    # Llaves foraneas
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id"), nullable=False)

    # metricas simples para auditoría y seguimiento
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con el modelo Ejercicio
    ejercicio = relationship("Ejercicio", back_populates="periodos_captura")
