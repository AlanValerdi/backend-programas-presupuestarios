from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas
from app.schemas.unidades import UnidadOut


router = APIRouter(prefix="/api/unidades", tags=["unidades"])


@router.get("", response_model=list[UnidadOut])
def listar_unidades(db: Session = Depends(get_db)):
    unidades = (
        db.query(CatalogoUnidadesAdministrativas)
        .order_by(CatalogoUnidadesAdministrativas.clave)
        .all()
    )
    return [
        {
            "id": u.id,
            "numero": u.clave,
            "nombre": u.nombre,
            "plazas": u.plazas or 0,
            "estado": "activa" if u.activo else "inactiva",
            "fechaCreacion": u.creado_en.isoformat() if u.creado_en else "",
        }
        for u in unidades
    ]


@router.get("/{numero}", response_model=UnidadOut)
def obtener_unidad(numero: str, db: Session = Depends(get_db)):
    unidad = (
        db.query(CatalogoUnidadesAdministrativas)
        .filter(CatalogoUnidadesAdministrativas.clave == numero)
        .first()
    )
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    return {
        "id": unidad.id,
        "numero": unidad.clave,
        "nombre": unidad.nombre,
        "plazas": unidad.plazas or 0,
        "estado": "activa" if unidad.activo else "inactiva",
        "fechaCreacion": unidad.creado_en.isoformat() if unidad.creado_en else "",
    }
