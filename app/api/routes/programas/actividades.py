from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import actividades as actividades_crud
from app.crud.programas import catalogo as catalogo_crud
from app.models.usuario import RolUsuario
from app.schemas.programas import ActividadOut
from app.services.programas.formatters import build_actividad_out, build_actividades_out

router = APIRouter()


@router.get("/actividades/{actividad_id}", response_model=ActividadOut)
def obtener_actividad(
    actividad_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    actividad = actividades_crud.get_actividad_by_id(db, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    if current_user.rol == RolUsuario.EJECUTOR:
        unidad_id = actividad.componente.programa.unidad_administrativa_id
        if unidad_id != current_user.unidad_administrativa_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

    return build_actividad_out(actividad)


@router.get("/{clave}/actividades", response_model=list[ActividadOut])
def listar_actividades(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    programas = catalogo_crud.get_programas_by_clave(db, clave, current_user)
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    prog_ids = [programa.id for programa in programas]
    actividades = actividades_crud.get_actividades_by_programa_ids(db, prog_ids)
    return build_actividades_out(actividades, programa_clave=clave)
