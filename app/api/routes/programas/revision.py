import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import avances as avances_crud
from app.models.programacion_avance import StatusAvance
from app.models.usuario import RolUsuario
from app.schemas.programas import RevisionInput
from app.services.programas.formatters import MESES_NOMBRES_LARGOS
from app.services.programas.trazabilidad import registrar_trazabilidad
from app.services.notifications import telegram as telegram_notifications

router = APIRouter()


@router.put("/actividades/{actividad_id}/mes/{mes}/revision")
def revisar_avance_mensual(
    actividad_id: int,
    mes: int,
    data: RevisionInput,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.rol not in [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR]:
        raise HTTPException(status_code=403, detail="No tienes permisos para realizar revisiones")

    meta = avances_crud.get_programacion_meta(db, actividad_id, mes)
    if not meta:
        raise HTTPException(status_code=404, detail="Programación mensual no encontrada")

    avance = avances_crud.get_avance_by_meta_id(db, meta.id)
    if not avance:
        raise HTTPException(status_code=404, detail="Avance no encontrado para este periodo")

    mes_nombre = MESES_NOMBRES_LARGOS.get(mes, f"Mes {mes}")

    if data.accion == "aprobar":
        avance.status = StatusAvance.FINALIZADO
        avance.comentarios_revision = None
        registrar_trazabilidad(
            db,
            avance.id,
            current_user.sub,
            "APROBAR",
            f"Avance del mes {mes_nombre} aprobado y finalizado",
        )
    elif data.accion == "devolver":
        avance.status = StatusAvance.CORRECCION
        avance.comentarios_revision = data.comentario
        registrar_trazabilidad(
            db,
            avance.id,
            current_user.sub,
            "RECHAZAR",
            f"Avance del mes {mes_nombre} devuelto para corrección. Comentario: {data.comentario}",
        )
    else:
        raise HTTPException(status_code=400, detail="Acción inválida. Use 'aprobar' o 'devolver'.")

    avance.fecha_revision = datetime.datetime.now()
    db.commit()

    try:
        telegram_notifications.notify_avance_revisado(
            db,
            actividad_id=actividad_id,
            mes=mes,
            accion=data.accion,
            actor_username=current_user.sub,
            comentario=data.comentario,
        )
    except Exception as error:
        print(f"Telegram notification failed: {error}")

    return {"status": "success", "message": f"Avance mensual revisado con éxito ({data.accion})"}
