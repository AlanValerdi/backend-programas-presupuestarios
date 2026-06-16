from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import settings as settings_crud
from app.models.usuario import RolUsuario

router = APIRouter()


@router.get("/config/settings")
def obtener_settings(db: Session = Depends(get_db)):
    ejercicio = settings_crud.get_ejercicio_activo(db)
    if not ejercicio:
        return {"mostrar_montos": True}
    return {"mostrar_montos": ejercicio.mostrar_montos}


@router.put("/config/settings")
def actualizar_settings(
    mostrar_montos: bool = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(status_code=403, detail="Permisos insuficientes.")

    ejercicio = settings_crud.get_ejercicio_activo(db)
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio activo no encontrado")

    ejercicio.mostrar_montos = mostrar_montos
    db.commit()
    return {"mostrar_montos": ejercicio.mostrar_montos}
