import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import TELEGRAM_LINK_TOKEN_EXPIRE_MINUTES
from app.models.telegram import UsuarioTelegramLink
from app.models.usuario import RolUsuario, Usuario


def hash_link_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_link_by_usuario_id(db: Session, usuario_id: int) -> UsuarioTelegramLink | None:
    return (
        db.query(UsuarioTelegramLink)
        .filter(UsuarioTelegramLink.usuario_id == usuario_id)
        .first()
    )


def get_or_create_link(db: Session, usuario_id: int) -> UsuarioTelegramLink:
    link = get_link_by_usuario_id(db, usuario_id)
    if link:
        return link

    link = UsuarioTelegramLink(usuario_id=usuario_id, is_active=False)
    db.add(link)
    db.flush()
    return link


def create_link_token(db: Session, usuario_id: int) -> tuple[str, UsuarioTelegramLink]:
    link = get_or_create_link(db, usuario_id)
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=TELEGRAM_LINK_TOKEN_EXPIRE_MINUTES)

    link.link_token_hash = hash_link_token(raw_token)
    link.link_token_expires_at = expires_at
    db.commit()
    db.refresh(link)
    return raw_token, link


def get_link_by_token_hash(db: Session, token_hash: str) -> UsuarioTelegramLink | None:
    return (
        db.query(UsuarioTelegramLink)
        .filter(UsuarioTelegramLink.link_token_hash == token_hash)
        .first()
    )


def activate_link(
    db: Session,
    link: UsuarioTelegramLink,
    *,
    chat_id: str,
    telegram_user_id: str | None,
    telegram_username: str | None,
) -> UsuarioTelegramLink:
    now = datetime.now(timezone.utc)
    link.telegram_chat_id = chat_id
    link.telegram_user_id = telegram_user_id
    link.telegram_username = telegram_username
    link.link_token_hash = None
    link.link_token_expires_at = None
    link.is_active = True
    link.linked_at = now
    link.last_message_at = now
    db.commit()
    db.refresh(link)
    return link


def deactivate_link(db: Session, link: UsuarioTelegramLink) -> UsuarioTelegramLink:
    link.is_active = False
    link.telegram_chat_id = None
    link.telegram_user_id = None
    link.telegram_username = None
    link.telegram_phone_number = None
    link.link_token_hash = None
    link.link_token_expires_at = None
    link.linked_at = None
    db.commit()
    db.refresh(link)
    return link


def update_last_message_at(db: Session, link: UsuarioTelegramLink) -> None:
    link.last_message_at = datetime.now(timezone.utc)
    db.commit()


def get_active_links_by_roles(db: Session, roles: list[str]) -> list[UsuarioTelegramLink]:
    return (
        db.query(UsuarioTelegramLink)
        .join(Usuario, UsuarioTelegramLink.usuario_id == Usuario.id)
        .filter(
            UsuarioTelegramLink.is_active == True,
            UsuarioTelegramLink.telegram_chat_id.isnot(None),
            Usuario.activo == True,
            Usuario.rol.in_(roles),
        )
        .all()
    )


def get_active_links_by_unidad(db: Session, unidad_id: int) -> list[UsuarioTelegramLink]:
    return (
        db.query(UsuarioTelegramLink)
        .join(Usuario, UsuarioTelegramLink.usuario_id == Usuario.id)
        .filter(
            UsuarioTelegramLink.is_active == True,
            UsuarioTelegramLink.telegram_chat_id.isnot(None),
            Usuario.activo == True,
            Usuario.rol == RolUsuario.EJECUTOR,
            Usuario.unidad_administrativa_id == unidad_id,
        )
        .all()
    )


def get_link_by_chat_id(db: Session, chat_id: str) -> UsuarioTelegramLink | None:
    return (
        db.query(UsuarioTelegramLink)
        .filter(UsuarioTelegramLink.telegram_chat_id == chat_id)
        .first()
    )


def get_active_link_by_usuario_id(db: Session, usuario_id: int) -> UsuarioTelegramLink | None:
    return (
        db.query(UsuarioTelegramLink)
        .filter(
            UsuarioTelegramLink.usuario_id == usuario_id,
            UsuarioTelegramLink.is_active == True,
            UsuarioTelegramLink.telegram_chat_id.isnot(None),
        )
        .first()
    )
