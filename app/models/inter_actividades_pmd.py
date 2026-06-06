from sqlalchemy import Column, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ActividadPMD(Base):
    __tablename__ = "inter_actividades_pmd"

    actividad_id = Column(Integer, ForeignKey("actividades.id"), primary_key=True)
    pmd_id = Column(Integer, ForeignKey("catalogo_pmd.id"), primary_key=True)