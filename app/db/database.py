from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Reemplaza con tus credenciales reales (idealmente usando variables de entorno)
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class para los modelos de SQLAlchemy
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()