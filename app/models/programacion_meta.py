from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ProgramacionMeta(Base):
    __tablename__ = "programacion_metas"

    id = Column(Integer, primary_key=True, index=True)
    cantidad_programada = Column(Integer, nullable=False) # cantidad programada para la actividad
    mes = Column(Integer, nullable=False, comment="Número del mes (1-12)") # mes al que corresponde la programación
    # monto_programado = Column(Numeric(15, 2), nullable=False) # monto


    # Llaves foraneas
    actividad_id = Column(Integer, ForeignKey("actividades.id"), nullable=False)

    # Relaciones 
    actividad = relationship("Actividades", back_populates="metas_mensuales")
    avance = relationship("ProgramacionAvance", back_populates="meta", uselist=False)
    
    # metricas
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())