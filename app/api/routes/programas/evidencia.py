import datetime
import os
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import actividades as actividades_crud
from app.crud.programas import avances as avances_crud
from app.crud.programas import evidencia as evidencia_crud
from app.models.programacion_avance import StatusAvance
from app.models.usuario import RolUsuario
from app.services.programas.evidencia import remove_evidencia_file, save_evidencia_file

router = APIRouter()

DELETABLE_EVIDENCIA_STATUSES = {StatusAvance.BORRADOR, StatusAvance.CORRECCION}


def _assert_ejecutor_access(actividad, current_user: TokenData) -> None:
    if current_user.rol != RolUsuario.EJECUTOR:
        return

    unidad_id = actividad.componente.programa.unidad_administrativa_id
    if unidad_id != current_user.unidad_administrativa_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")


def can_delete_evidencia(status: StatusAvance | None) -> bool:
    return status in DELETABLE_EVIDENCIA_STATUSES


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


@router.post("/actividades/{actividad_id}/mes/{mes}/evidencia-draft")
def guardar_evidencia_borrador(
    actividad_id: int,
    mes: int,
    avance_meta: int = Form(0),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if not files or not any(file and file.filename for file in files):
        raise HTTPException(status_code=400, detail="Debe adjuntar al menos un archivo")

    actividad = actividades_crud.get_actividad_by_id(db, actividad_id)
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    _assert_ejecutor_access(actividad, current_user)

    meta = avances_crud.get_programacion_meta(db, actividad_id, mes)
    if not meta:
        raise HTTPException(status_code=404, detail="Programación mensual no encontrada")

    periodo = avances_crud.get_captura_periodo(db, mes)
    if not periodo:
        raise HTTPException(status_code=400, detail="Periodo de captura no configurado")

    now = datetime.datetime.now()
    if not (periodo.fecha_inicio_reporte <= now <= periodo.fecha_fin_reporte):
        raise HTTPException(
            status_code=400,
            detail=(
                "El periodo de captura para este mes no está activo "
                f"({periodo.fecha_inicio_reporte.strftime('%d/%m/%Y')} - "
                f"{periodo.fecha_fin_reporte.strftime('%d/%m/%Y')})"
            ),
        )

    avance = avances_crud.get_avance_by_meta_id(db, meta.id)

    if not avance:
        avance = avances_crud.create_draft_avance(db, meta.id, avance_meta)
    else:
        if avance.status == StatusAvance.FINALIZADO:
            raise HTTPException(
                status_code=400,
                detail="El avance de este mes ya ha sido finalizado y aprobado",
            )
        if avance.status == StatusAvance.ENVIADO:
            raise HTTPException(
                status_code=400,
                detail="No se pueden agregar evidencias en borrador mientras el avance está en revisión",
            )

        if avance.avance_meta != avance_meta:
            avance.avance_meta = avance_meta

    uploaded_count = 0
    for file in files:
        if file and file.filename:
            evidencia = save_evidencia_file(file, avance.id)
            db.add(evidencia)
            db.flush()
            uploaded_count += 1

    db.commit()

    return {
        "status": "success",
        "message": f"{uploaded_count} archivo(s) guardado(s) en borrador",
        "uploaded_count": uploaded_count,
    }


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

    if not can_delete_evidencia(avance.status):
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden eliminar documentos en borrador o devueltos para corrección.",
        )

    ev.activo = False

    try:
        remove_evidencia_file(ev.url_archivo)
    except Exception as error:
        print(f"Error removing physical file: {error}")

    db.commit()

    return {"status": "success", "message": "Evidencia eliminada"}
