import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import TokenData, require_entidad_match, get_db
from app.crud.programas import avances as avances_crud
from app.models.programacion_avance import StatusAvance
from app.services.programas.evidencia import save_evidencia_file
from app.services.programas.formatters import MESES_NOMBRES_LARGOS
from app.services.programas.trazabilidad import registrar_trazabilidad
from app.services.notifications import telegram as telegram_notifications

router = APIRouter()


@router.post("/actividades/{actividad_id}/mes/{mes}/avance")
def guardar_avance_mensual(
    actividad_id: int,
    mes: int,
    avance_meta: int = Form(...),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
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
    mes_nombre = MESES_NOMBRES_LARGOS.get(mes, f"Mes {mes}")

    if not avance:
        avance = avances_crud.create_avance(db, meta.id, avance_meta, now)
        registrar_trazabilidad(
            db,
            avance.id,
            current_user.sub,
            "ENVIAR",
            f"Avance del mes {mes_nombre} enviado a revisión con meta de {avance_meta}",
        )
    else:
        if avance.status == StatusAvance.FINALIZADO:
            raise HTTPException(
                status_code=400,
                detail="El avance de este mes ya ha sido finalizado y aprobado",
            )

        if avance.avance_meta != avance_meta:
            registrar_trazabilidad(
                db,
                avance.id,
                current_user.sub,
                "MODIFICAR_META",
                f"Meta del avance del mes {mes_nombre} modificada de {avance.avance_meta} a {avance_meta}",
            )

        avance.avance_meta = avance_meta
        avance.status = StatusAvance.ENVIADO
        avance.fecha_envio = now
        registrar_trazabilidad(
            db,
            avance.id,
            current_user.sub,
            "ENVIAR",
            f"Avance del mes {mes_nombre} enviado a revisión con meta de {avance_meta}",
        )

    for file in files:
        if file and file.filename:
            evidencia = save_evidencia_file(file, avance.id)
            db.add(evidencia)
            db.flush()
            registrar_trazabilidad(
                db,
                avance.id,
                current_user.sub,
                "ENVIAR",
                f"Archivo de evidencia '{file.filename}' adjuntado al avance del mes {mes_nombre}",
            )

    db.commit()

    try:
        telegram_notifications.notify_avance_enviado(
            db,
            actividad_id=actividad_id,
            mes=mes,
            avance_meta=avance_meta,
            actor_username=current_user.sub,
        )
    except Exception as error:
        print(f"Telegram notification failed: {error}")

    return {"status": "success", "message": "Avance mensual guardado y enviado a revisión"}
