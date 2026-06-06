import enum
from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, Numeric, String, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

# Definimos los estados que mencionaste para el flujo de aprobación
class StatusAvance(str, enum.Enum):
    BORRADOR = "BORRADOR"
    ENVIADO = "ENVIADO"
    CORRECCION = "CORRECCION"
    FINALIZADO = "FINALIZADO"

class ProgramacionAvance(Base):
    __tablename__ = "programacion_avances"

    id = Column(Integer, primary_key=True, index=True)
    avance_meta = Column(Integer, default=0, comment="Cantidad real alcanzada")
    # avance_financiero = Column(Numeric(15, 2), default=0.00, comment="Dinero real gastado")
    observaciones = Column(Text, nullable=True)
    
    # 3. EL FLUJO DE TRABAJO (Workflow)
    status = Column(Enum(StatusAvance), default=StatusAvance.BORRADOR)
    fecha_envio = Column(DateTime(timezone=True), nullable=True)
    fecha_revision = Column(DateTime(timezone=True), nullable=True)
    comentarios_revision = Column(Text, nullable=True, comment="Feedback del revisor si lo rechaza")
    
    # Llaves foraneas
    programacion_meta_id = Column(Integer, ForeignKey("programacion_metas.id"), unique=True, nullable=False)
    
    # Relaciones
    meta = relationship("ProgramacionMeta", back_populates="avance")
    evidencias = relationship("ProgramacionEvidencia", back_populates="avance")

    # metricas
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

  