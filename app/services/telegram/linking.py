from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import TELEGRAM_BOT_USERNAME
from app.crud import crud_telegram
from app.models.telegram import UsuarioTelegramLink
from app.services.telegram.client import send_message


def build_deep_link(raw_token: str) -> str:
    bot_username = TELEGRAM_BOT_USERNAME.lstrip("@")
    return f"https://t.me/{bot_username}?start={raw_token}"


def get_link_status(link: UsuarioTelegramLink | None) -> dict:
    if not link:
        return {
            "is_linked": False,
            "is_active": False,
            "linked_at": None,
            "telegram_username": None,
            "has_pending_token": False,
            "token_expires_at": None,
        }

    now = datetime.now(timezone.utc)
    has_pending_token = bool(
        link.link_token_hash
        and link.link_token_expires_at
        and link.link_token_expires_at > now
    )

    return {
        "is_linked": bool(link.telegram_chat_id and link.is_active),
        "is_active": link.is_active,
        "linked_at": link.linked_at,
        "telegram_username": link.telegram_username,
        "has_pending_token": has_pending_token,
        "token_expires_at": link.link_token_expires_at if has_pending_token else None,
    }


def process_start_command(
    db: Session,
    *,
    token: str,
    chat_id: str,
    telegram_user_id: str | None,
    telegram_username: str | None,
) -> tuple[bool, str]:
    token_hash = crud_telegram.hash_link_token(token)
    link = crud_telegram.get_link_by_token_hash(db, token_hash)
    if not link:
        return False, "Token de vinculacion invalido o expirado."

    now = datetime.now(timezone.utc)
    if not link.link_token_expires_at or link.link_token_expires_at < now:
        return False, "El token de vinculacion ha expirado. Genera uno nuevo en la webapp."

    if link.telegram_chat_id and link.telegram_chat_id != chat_id and link.is_active:
        return False, "Esta cuenta ya esta vinculada a otro chat de Telegram."

    crud_telegram.activate_link(
        db,
        link,
        chat_id=chat_id,
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
    )
    return True, "Cuenta vinculada correctamente. Recibiras notificaciones de movimientos."


def process_stop_command(db: Session, chat_id: str) -> tuple[bool, str]:
    link = crud_telegram.get_link_by_chat_id(db, chat_id)
    if not link or not link.is_active:
        return False, "No hay una cuenta vinculada en este chat."

    crud_telegram.deactivate_link(db, link)
    return True, "Notificaciones desactivadas. Puedes volver a vincular desde la webapp."


def send_safe_message(chat_id: str, text: str) -> None:
    send_message(chat_id, text)
