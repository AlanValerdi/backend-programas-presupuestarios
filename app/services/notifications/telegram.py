import logging
import re

from sqlalchemy.orm import Session

from app.crud import crud_telegram
from app.crud.programas import actividades as actividades_crud
from app.models.usuario import RolUsuario
from app.services.programas.formatters import MESES_NOMBRES_LARGOS
from app.services.telegram.client import send_message

logger = logging.getLogger(__name__)

MARKDOWN_ESCAPE_PATTERN = re.compile(r"([_*`\[])")


def _escape_markdown(text: str) -> str:
    return MARKDOWN_ESCAPE_PATTERN.sub(r"\\\1", text)


def _bold(text: str) -> str:
    return f"**{_escape_markdown(text)}**"


def _send_to_links(links, message: str) -> None:
    for link in links:
        if not link.telegram_chat_id:
            continue
        sent = send_message(link.telegram_chat_id, message, parse_mode="Markdown")
        if not sent:
            logger.warning(
                "Telegram notification failed for usuario_id=%s chat_id=%s",
                link.usuario_id,
                link.telegram_chat_id,
            )


def _get_activity_context(db: Session, actividad_id: int) -> dict | None:
    actividad = actividades_crud.get_actividad_by_id(db, actividad_id)
    if not actividad or not actividad.componente or not actividad.componente.programa:
        return None

    programa = actividad.componente.programa
    return {
        "actividad_clave": actividad.clave,
        "actividad_nombre": actividad.descripcion,
        "componente_clave": actividad.componente.clave,
        "componente_nombre": actividad.componente.descripcion,
        "programa_clave": programa.clave,
        "programa_nombre": programa.programa,
        "unidad_id": programa.unidad_administrativa_id,
    }


def _format_context_lines(context: dict) -> str:
    return (
        f"Programa: {context['programa_clave']} - {context['programa_nombre']}\n"
        f"Componente: {context['componente_clave']} - {context['componente_nombre']}\n"
        f"Actividad: {context['actividad_clave']} - {context['actividad_nombre']}"
    )


def notify_avance_enviado(
    db: Session,
    *,
    actividad_id: int,
    mes: int,
    avance_meta: int,
    actor_username: str,
) -> None:
    context = _get_activity_context(db, actividad_id)
    if not context:
        return

    mes_nombre = MESES_NOMBRES_LARGOS.get(mes, f"Mes {mes}")
    message = (
        f"{_bold('Nuevo avance enviado a revision')}\n"
        f"{_bold(f'Meta reportada: {avance_meta}')}\n"
        f"{_format_context_lines(context)}\n"
        f"Mes: {mes_nombre}\n"
        f"Enviado por: {actor_username}"
    )

    links = crud_telegram.get_active_links_by_roles(
        db,
        [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR],
    )
    _send_to_links(links, message)


def notify_avance_revisado(
    db: Session,
    *,
    actividad_id: int,
    mes: int,
    accion: str,
    actor_username: str,
    comentario: str | None = None,
) -> None:
    context = _get_activity_context(db, actividad_id)
    if not context or not context["unidad_id"]:
        return

    mes_nombre = MESES_NOMBRES_LARGOS.get(mes, f"Mes {mes}")

    if accion == "aprobar":
        title = _bold("Avance aprobado")
        extra_lines = ""
    else:
        title = _bold("Avance devuelto para correccion")
        extra_lines = f"{_bold(f'Comentario: {comentario or ''}')}\n" if comentario else ""

    message = (
        f"{title}\n"
        f"{extra_lines}"
        f"{_format_context_lines(context)}\n"
        f"Mes: {mes_nombre}\n"
        f"Revisado por: {actor_username}"
    )

    links = crud_telegram.get_active_links_by_unidad(db, context["unidad_id"])
    _send_to_links(links, message)


def notify_evidencia_eliminada(
    db: Session,
    *,
    actividad_id: int,
    mes: int,
    nombre_archivo: str,
    actor_username: str,
) -> None:
    context = _get_activity_context(db, actividad_id)
    if not context:
        return

    mes_nombre = MESES_NOMBRES_LARGOS.get(mes, f"Mes {mes}")
    message = (
        f"{_bold('Evidencia eliminada')}\n"
        f"{_bold(f'Archivo: {nombre_archivo}')}\n"
        f"{_format_context_lines(context)}\n"
        f"Mes: {mes_nombre}\n"
        f"Eliminado por: {actor_username}"
    )

    links = crud_telegram.get_active_links_by_roles(
        db,
        [RolUsuario.PLANEACION, RolUsuario.ADMINISTRADOR],
    )
    _send_to_links(links, message)
