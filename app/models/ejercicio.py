from sqlalchemy import Column, Integer, Date, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Ejercicio(Base):
    __tablename__ = "ejercicios"
    __table_args__ = (
        UniqueConstraint("entidad_id", "anio", name="uq_ejercicios_entidad_anio"),
    )

    id = Column(Integer, primary_key=True, index=True)
    anio = Column(Integer, nullable=False)
    entidad_id = Column(Integer, ForeignKey("entidades.id"), nullable=False, index=True)
    
    # FECHAS DE PLANEACIÓN (Para crear Programas, Componentes, Actividades)
    fecha_inicio_planeacion = Column(DateTime, comment="Cuándo abre el sistema para armar el POA")
    fecha_fin_planeacion = Column(DateTime, comment="Cuándo cierra la creación de programas")
    planeacion_abierta = Column(Boolean, default=False, comment="Switch manual de emergencia")
    mostrar_montos = Column(Boolean, default=True, server_default="true", comment="Permite ocultar/mostrar montos en el sistema")
    
    # El estatus general del año fiscal
    activo = Column(Boolean, default=True)

    # Relaciones
    entidad = relationship("Entidad")
    periodos_captura = relationship("CapturaPeriodos", back_populates="ejercicio")
    techos_financieros = relationship("TechoFinanciero", back_populates="ejercicio")
    programas = relationship("CatalogoProgramas", back_populates="ejercicio")

    # metricas
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
