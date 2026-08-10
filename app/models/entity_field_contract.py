from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class EntityType:
    PROGRAMA = "programa"
    ACTIVIDAD = "actividad"


class EntityFieldContract(Base):
    __tablename__ = "entity_field_contracts"
    __table_args__ = (
        UniqueConstraint("entidad_id", "entity_type", name="uq_entity_field_contracts_entidad_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    entidad_id = Column(Integer, ForeignKey("entidades.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    # List of {key, label, type, required}
    fields = Column(JSONB, nullable=False, server_default="[]")
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    entidad = relationship("Entidad", back_populates="field_contracts")
