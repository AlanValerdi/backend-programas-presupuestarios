import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import evidencia as evidencia_crud
from app.models.programacion_avance import StatusAvance
from app.models.usuario import RolUsuario
from app.services.programas.evidencia import remove_evidencia_file
from app.services.programas.formatters import MESES_NOMBRES_LARGOS
from app.services.programas.trazabilidad import registrar_trazabilidad
from app.services.notifications import telegram as telegram_notifications

router = APIRouter()


@router.get("/evidencia/download/{evidencia_id}")
def descargar_evidencia(
    evidencia_id: int,
    db: Session = Depends(get_db),
):
    ev = evidencia_crud.get_evidencia_by_id(db, evidencia_id)
    if not ev or not ev.activo:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    if not os.path.exists(ev.url_archivo):
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado en el servidor")

    return FileResponse(ev.url_archivo, filename=ev.nombre_original, media_type=ev.mime_type)


@router.delete("/evidencia/{evidencia_id}")
def eliminar_evidencia(
    evidencia_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    ev = evidencia_crud.get_evidencia_by_id(db, evidencia_id)
    if not ev or not ev.activo:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    avance = ev.avance
    if not avance:
        raise HTTPException(status_code=404, detail="Avance no encontrado para esta evidencia")

    if current_user.rol == RolUsuario.EJECUTOR:
        meta = avance.meta
        if meta and meta.actividad:
            unidad_id = meta.actividad.componente.programa.unidad_administrativa_id
            if unidad_id != current_user.unidad_administrativa_id:
                raise HTTPException(status_code=403, detail="Acceso denegado")

        if avance.status != StatusAvance.CORRECCION:
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden eliminar documentos de avances devueltos para corrección.",
            )

    ev.activo = False

    try:
        remove_evidencia_file(ev.url_archivo)
    except Exception as error:
        print(f"Error removing physical file: {error}")

    mes_nombre = MESES_NOMBRES_LARGOS.get(avance.meta.mes, f"Mes {avance.meta.mes}")
    registrar_trazabilidad(
        db,
        avance.id,
        current_user.sub,
        "ELIMINAR_ARCHIVO",
        f"Archivo de evidencia '{ev.nombre_original}' eliminado del avance del mes {mes_nombre}",
    )
    db.commit()

    try:
        telegram_notifications.notify_evidencia_eliminada(
            db,
            actividad_id=avance.meta.actividad_id,
            mes=avance.meta.mes,
            nombre_archivo=ev.nombre_original,
            actor_username=current_user.sub,
        )
    except Exception as error:
        print(f"Telegram notification failed: {error}")

    return {"status": "success", "message": "Evidencia eliminada y registrada en trazabilidad"}
