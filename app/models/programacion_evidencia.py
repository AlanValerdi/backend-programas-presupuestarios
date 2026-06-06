from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ProgramacionEvidencia(Base):
    __tablename__ = "programacion_evidencias"

    id = Column(Integer, primary_key=True, index=True)
    
    # Llave foránea
    programacion_avance_id = Column(Integer, ForeignKey("programacion_avances.id"), nullable=False)
    
    # Datos del archivo
    nombre_original = Column(String, nullable=False, comment="Ej. reporte_enero_final.pdf")
    url_archivo = Column(String, nullable=False, comment="Ruta en el servidor: /uploads/2026/01/reporte.pdf")
    mime_type = Column(String, nullable=False, comment="Ej. application/pdf, image/jpeg")
    
    # Auditoría estándar
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación inversa
    avance = relationship("ProgramacionAvance", back_populates="evidencias")