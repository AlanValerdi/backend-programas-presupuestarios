from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.api.routes.etl import router as etl_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.programas import router as programas_router
from app.api.routes.fechas_captura import router as fechas_captura_router
from app.api.routes.usuarios import router as usuarios_router
from app.core.config import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD
from app.core.security import hashear_password
from app.db.database import SessionLocal
from app.models.usuario import Usuario, RolUsuario


@asynccontextmanager
async def lifespan(app: FastAPI):
    db: Session = SessionLocal()
    try:
        admin_exists = db.query(Usuario).filter(Usuario.rol == RolUsuario.ADMINISTRADOR).first()
        if not admin_exists:
            admin = Usuario(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=hashear_password(ADMIN_PASSWORD),
                rol=RolUsuario.ADMINISTRADOR,
                activo=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(etl_router)
app.include_router(unidades_router)
app.include_router(programas_router)
app.include_router(fechas_captura_router)
app.include_router(usuarios_router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

