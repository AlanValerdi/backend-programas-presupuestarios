from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, require_any_role, TokenData, get_entidad_from_slug
from app.models.catalogo_unidades_administrativas import CatalogoUnidadesAdministrativas
from app.models.entidad import Entidad
from app.schemas.unidades import UnidadOut


router = APIRouter(prefix="/unidades", tags=["unidades"])


@router.get("", response_model=list[UnidadOut])
def listar_unidades(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_any_role()),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    unidades = (
        db.query(CatalogoUnidadesAdministrativas)
        .filter(CatalogoUnidadesAdministrativas.entidad_id == entidad.id)
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
def obtener_unidad(
    numero: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_any_role()),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    unidad = (
        db.query(CatalogoUnidadesAdministrativas)
        .filter(
            CatalogoUnidadesAdministrativas.clave == numero,
            CatalogoUnidadesAdministrativas.entidad_id == entidad.id,
        )
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
