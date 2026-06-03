from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class CatalogoProgramas(Base):
    __tablename__ = "catalogo_programas"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String, nullable=False) # clave del programa presupuestal
    programa = Column(String, nullable=False) # TBD: Los programas deberian venir de un catalogo, pero por ahora lo dejamos como string

    # Relaciones 
    # ejecutor = 