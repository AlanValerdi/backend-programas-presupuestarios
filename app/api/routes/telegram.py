from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, require_entidad_match, get_db
from app.core.config import TELEGRAM_BOT_USERNAME, TELEGRAM_WEBHOOK_SECRET
from app.crud import crud_telegram, crud_usuario
from app.schemas.telegram import (
    TelegramLinkActionOut,
    TelegramLinkGenerateOut,
    TelegramLinkStatusOut,
)
from app.services.telegram.linking import (
    build_deep_link,
    get_link_status,
    process_start_command,
    process_stop_command,
    send_safe_message,
)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/link/status", response_model=TelegramLinkStatusOut)
def get_telegram_link_status(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
    user = crud_usuario.get_usuario_by_username(db, current_user.sub, current_user.entidad_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    link = crud_telegram.get_link_by_usuario_id(db, user.id)
    return get_link_status(link)


@router.post("/link/generate", response_model=TelegramLinkGenerateOut)
def generate_telegram_link(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
    if not TELEGRAM_BOT_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot username is not configured",
        )

    user = crud_usuario.get_usuario_by_username(db, current_user.sub, current_user.entidad_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    raw_token, link = crud_telegram.create_link_token(db, user.id)
    return {
        "deep_link": build_deep_link(raw_token),
        "expires_at": link.link_token_expires_at,
        "bot_username": TELEGRAM_BOT_USERNAME.lstrip("@"),
    }


@router.delete("/link", response_model=TelegramLinkActionOut)
def unlink_telegram(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
    user = crud_usuario.get_usuario_by_username(db, current_user.sub, current_user.entidad_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    link = crud_telegram.get_link_by_usuario_id(db, user.id)
    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="No linked Telegram account found")

    chat_id = link.telegram_chat_id
    crud_telegram.deactivate_link(db, link)

    if chat_id:
        send_safe_message(chat_id, "Tu cuenta fue desvinculada de las notificaciones.")

    return {"status": "success", "message": "Telegram account unlinked"}


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if TELEGRAM_WEBHOOK_SECRET and x_telegram_bot_api_secret_token != TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    payload = await request.json()
    message = payload.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    sender = message.get("from") or {}

    chat_id = str(chat.get("id")) if chat.get("id") is not None else None
    if not chat_id or not text:
        return {"ok": True}

    telegram_user_id = str(sender.get("id")) if sender.get("id") is not None else None
    telegram_username = sender.get("username")

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_safe_message(
                chat_id,
                "Para vincular tu cuenta, abre el enlace desde la webapp e inicia el bot con el token.",
            )
            return {"ok": True}

        success, response_message = process_start_command(
            db,
            token=parts[1].strip(),
            chat_id=chat_id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
        )
        send_safe_message(chat_id, response_message)
        return {"ok": success}

    if text.startswith("/stop"):
        success, response_message = process_stop_command(db, chat_id)
        send_safe_message(chat_id, response_message)
        return {"ok": success}

    send_safe_message(
        chat_id,
        "Este bot solo envia notificaciones. Usa /stop para desactivarlas.",
    )
    return {"ok": True}
