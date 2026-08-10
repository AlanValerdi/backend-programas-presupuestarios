from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.api.routes.etl import router as etl_router
from app.api.routes.unidades import router as unidades_router
from app.api.routes.programas import router as programas_router
from app.api.routes.fechas_captura import router as fechas_captura_router
from app.api.routes.usuarios import router as usuarios_router
from app.api.routes.telegram import router as telegram_router
from app.api.routes.contracts import router as contracts_router
from app.core.config import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD
from app.core.security import hashear_password
from app.db.database import SessionLocal
from app.models.usuario import Usuario, RolUsuario
from app.models.entidad import Entidad


@asynccontextmanager
async def lifespan(app: FastAPI):
    db: Session = SessionLocal()
    try:
        huachinango = (
            db.query(Entidad).filter(Entidad.slug == "huachinango").first()
        )
        if huachinango:
            admin_exists = (
                db.query(Usuario)
                .filter(
                    Usuario.rol == RolUsuario.ADMINISTRADOR,
                    Usuario.entidad_id == huachinango.id,
                )
                .first()
            )
            if not admin_exists:
                admin = Usuario(
                    username=ADMIN_USERNAME,
                    email=ADMIN_EMAIL,
                    hashed_password=hashear_password(ADMIN_PASSWORD),
                    rol=RolUsuario.ADMINISTRADOR,
                    activo=True,
                    entidad_id=huachinango.id,
                )
                db.add(admin)
                db.commit()
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://programas-presupuestales-e5n4sj036-alan-valerdis-projects.vercel.app", "https://programas-presupuestales-psi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

entity_router = APIRouter(prefix="/api/e/{entidad_slug}")
entity_router.include_router(etl_router)
entity_router.include_router(unidades_router)
entity_router.include_router(programas_router)
entity_router.include_router(fechas_captura_router)
entity_router.include_router(usuarios_router)
entity_router.include_router(telegram_router)
entity_router.include_router(contracts_router)

app.include_router(entity_router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
