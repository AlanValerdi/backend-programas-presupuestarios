from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import avances as avances_crud
from app.crud.programas import trazabilidad as trazabilidad_crud

router = APIRouter()


@router.get("/actividades/{actividad_id}/mes/{mes}/trazabilidad")
def obtener_trazabilidad(
    actividad_id: int,
    mes: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    meta = avances_crud.get_programacion_meta(db, actividad_id, mes)
    if not meta:
        return []

    avance = avances_crud.get_avance_by_meta_id(db, meta.id)
    if not avance:
        return []

    logs = trazabilidad_crud.get_trazabilidad_logs_by_avance_id(db, avance.id)
    return [
        {
            "id": log.id,
            "usuario": log.usuario.username if log.usuario else "Sistema",
            "rol": log.usuario.rol if log.usuario else "sistema",
            "accion": log.accion,
            "detalles": log.detalles,
            "creadoEn": log.creado_en.isoformat() if log.creado_en else "",
        }
        for log in logs
    ]


@router.get("/trazabilidad")
def obtener_trazabilidad_global(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    logs = trazabilidad_crud.get_trazabilidad_global(db)
    return [
        {
            "id": log.id,
            "usuario": log.usuario.username if log.usuario else "Sistema",
            "rol": log.usuario.rol if log.usuario else "sistema",
            "accion": log.accion,
            "detalles": log.detalles,
            "creadoEn": log.creado_en.isoformat() if log.creado_en else "",
            "mes": mes,
            "actividadClave": actividad_clave,
            "componenteClave": componente_clave,
            "programaClave": programa_clave,
            "programaNombre": programa_nombre,
        }
        for log, mes, actividad_clave, componente_clave, programa_clave, programa_nombre in logs
    ]
