from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import catalogo as catalogo_crud
from app.crud.programas import presupuesto as presupuesto_crud
from app.models.usuario import RolUsuario
from app.schemas.programas import ProgramaOut
from app.services.programas.formatters import (
    aggregate_programas_grouped,
    build_programa_out_from_group,
)

router = APIRouter()


def _presupuesto_fn(db: Session):
    def fn(unidad_id: int, ejercicio_id: int) -> dict:
        return presupuesto_crud.obtener_presupuesto_programa(db, unidad_id, ejercicio_id)

    return fn


def listar_programas(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    programas = catalogo_crud.list_programas(db, current_user)
    return aggregate_programas_grouped(programas, _presupuesto_fn(db))


@router.get("/{clave}", response_model=ProgramaOut)
def obtener_programa(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    programas = catalogo_crud.get_programas_by_clave(db, clave, current_user)
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")
    return build_programa_out_from_group(programas, _presupuesto_fn(db))


@router.put("/{clave}/estado", response_model=ProgramaOut)
def actualizar_estado_programa(
    clave: str,
    estado: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes. Requiere rol planeacion o administrador.",
        )

    programas = catalogo_crud.get_programas_by_clave(db, clave, current_user)
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    estados_validos = ["configuracion", "en_captura", "en_revision", "finalizado"]
    if estado not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Debe ser uno de: {estados_validos}",
        )

    catalogo_crud.update_estado_programa(db, clave, estado)
    programas = catalogo_crud.get_programas_by_clave(db, clave, current_user)
    return build_programa_out_from_group(programas, _presupuesto_fn(db))
