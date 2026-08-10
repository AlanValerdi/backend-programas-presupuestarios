from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, require_entidad_match, get_db, get_entidad_from_slug
from app.crud.programas import settings as settings_crud
from app.models.usuario import RolUsuario
from app.models.entidad import Entidad

router = APIRouter()


@router.get("/config/settings")
def obtener_settings(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    ejercicio = settings_crud.get_ejercicio_activo(db, entidad.id)
    if not ejercicio:
        return {"mostrar_montos": True}
    return {"mostrar_montos": ejercicio.mostrar_montos}


@router.put("/config/settings")
def actualizar_settings(
    mostrar_montos: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes.")

    ejercicio = settings_crud.get_ejercicio_activo(db, entidad.id)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio activo no encontrado")

    ejercicio.mostrar_montos = mostrar_montos
    db.commit()
    return {"mostrar_montos": ejercicio.mostrar_montos}
