from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class UsuarioTelegramLink(Base):
    __tablename__ = "usuario_telegram_links"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    telegram_chat_id = Column(String(50), unique=True, nullable=True)
    telegram_user_id = Column(String(50), nullable=True)
    telegram_username = Column(String(100), nullable=True)
    telegram_phone_number = Column(String(20), nullable=True)
    link_token_hash = Column(String(64), nullable=True, index=True)
    link_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    linked_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    usuario = relationship("Usuario", backref="telegram_link")
