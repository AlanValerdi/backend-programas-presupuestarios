from sqlalchemy import Column, Integer, Date, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Ejercicio(Base):
    __tablename__ = "ejercicios"

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, unique=True, nullable=False)
    
    # FECHAS DE PLANEACIÓN (Para crear Programas, Componentes, Actividades)
    fecha_inicio_planeacion = Column(DateTime, comment="Cuándo abre el sistema para armar el POA")
    fecha_fin_planeacion = Column(DateTime, comment="Cuándo cierra la creación de programas")
    planeacion_abierta = Column(Boolean, default=False, comment="Switch manual de emergencia")
    
    # El estatus general del año fiscal
    activo = Column(Boolean, default=True)

    # Relaciones
    periodos_captura = relationship("CapturaPeriodos", back_populates="ejercicio")
    techos_financieros = relationship("TechoFinanciero", back_populates="ejercicio")
    programas = relationship("CatalogoProgramas", back_populates="ejercicio")

    # metricas
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())