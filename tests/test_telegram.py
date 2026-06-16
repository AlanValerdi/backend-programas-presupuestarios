from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import TELEGRAM_WEBHOOK_SECRET
from app.crud import crud_telegram
from app.main import app
from app.models.telegram import UsuarioTelegramLink
from app.services.telegram.linking import process_start_command, process_stop_command


client = TestClient(app)

EXPECTED_TELEGRAM_ROUTES = {
    ("GET", "/api/telegram/link/status"),
    ("POST", "/api/telegram/link/generate"),
    ("DELETE", "/api/telegram/link"),
    ("POST", "/api/telegram/webhook"),
}


def _collect_telegram_routes() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        if not hasattr(route, "methods"):
            continue
        path = getattr(route, "path", "")
        if not path.startswith("/api/telegram"):
            continue
        for method in route.methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.add((method, path))
    return routes


class TestTelegramRouteRegistration:
    def test_expected_telegram_routes_are_registered(self):
        registered = _collect_telegram_routes()
        assert EXPECTED_TELEGRAM_ROUTES.issubset(registered)


class TestTelegramLinkToken:
    def test_hash_link_token_is_deterministic(self):
        token = "sample-token"
        assert crud_telegram.hash_link_token(token) == crud_telegram.hash_link_token(token)
        assert crud_telegram.hash_link_token(token) != crud_telegram.hash_link_token("other-token")

    def test_process_start_command_activates_valid_token(self):
        db = MagicMock()
        now = datetime.now(timezone.utc)
        link = UsuarioTelegramLink(
            id=1,
            usuario_id=10,
            link_token_hash=crud_telegram.hash_link_token("valid-token"),
            link_token_expires_at=now + timedelta(minutes=10),
            is_active=False,
        )

        with patch("app.services.telegram.linking.crud_telegram.get_link_by_token_hash", return_value=link), patch(
            "app.services.telegram.linking.crud_telegram.activate_link",
            return_value=link,
        ) as activate_mock:
            success, message = process_start_command(
                db,
                token="valid-token",
                chat_id="123456",
                telegram_user_id="999",
                telegram_username="testuser",
            )

        assert success is True
        assert "vinculada" in message.lower()
        activate_mock.assert_called_once()

    def test_process_start_command_rejects_expired_token(self):
        db = MagicMock()
        link = UsuarioTelegramLink(
            id=1,
            usuario_id=10,
            link_token_hash=crud_telegram.hash_link_token("expired-token"),
            link_token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            is_active=False,
        )

        with patch("app.services.telegram.linking.crud_telegram.get_link_by_token_hash", return_value=link):
            success, message = process_start_command(
                db,
                token="expired-token",
                chat_id="123456",
                telegram_user_id="999",
                telegram_username="testuser",
            )

        assert success is False
        assert "expirado" in message.lower()

    def test_process_stop_command_deactivates_active_link(self):
        db = MagicMock()
        link = UsuarioTelegramLink(
            id=1,
            usuario_id=10,
            telegram_chat_id="123456",
            is_active=True,
        )

        with patch("app.services.telegram.linking.crud_telegram.get_link_by_chat_id", return_value=link), patch(
            "app.services.telegram.linking.crud_telegram.deactivate_link",
            return_value=link,
        ) as deactivate_mock:
            success, message = process_stop_command(db, "123456")

        assert success is True
        deactivate_mock.assert_called_once_with(db, link)
        assert "desactivadas" in message.lower()


class TestTelegramWebhookSecurity:
    def test_webhook_rejects_invalid_secret(self, monkeypatch):
        monkeypatch.setattr("app.api.routes.telegram.TELEGRAM_WEBHOOK_SECRET", "expected-secret")

        response = client.post(
            "/api/telegram/webhook",
            json={"message": {"text": "/start token", "chat": {"id": 1}}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )

        assert response.status_code == 403

    def test_webhook_accepts_valid_secret(self, monkeypatch):
        monkeypatch.setattr("app.api.routes.telegram.TELEGRAM_WEBHOOK_SECRET", "expected-secret")

        with patch("app.api.routes.telegram.send_safe_message") as send_mock:
            response = client.post(
                "/api/telegram/webhook",
                json={"message": {"text": "/start", "chat": {"id": 1}}},
                headers={"X-Telegram-Bot-Api-Secret-Token": "expected-secret"},
            )

        assert response.status_code == 200
        assert response.json() == {"ok": True}
        send_mock.assert_called_once()


class TestTelegramNotificationFailureIsolation:
    SAMPLE_CONTEXT = {
        "actividad_clave": "C1.A5",
        "actividad_nombre": "Actividad de prueba",
        "componente_clave": "C1",
        "componente_nombre": "Componente de prueba",
        "programa_clave": "P1",
        "programa_nombre": "Programa test",
        "unidad_id": 1,
    }

    def test_notify_avance_enviado_does_not_raise_when_send_fails(self):
        db = MagicMock()

        with patch(
            "app.services.notifications.telegram._get_activity_context",
            return_value=self.SAMPLE_CONTEXT,
        ), patch(
            "app.services.notifications.telegram.crud_telegram.get_active_links_by_roles",
            return_value=[UsuarioTelegramLink(id=1, usuario_id=2, telegram_chat_id="123", is_active=True)],
        ), patch(
            "app.services.notifications.telegram.send_message",
            return_value=False,
        ) as send_mock:
            from app.services.notifications.telegram import notify_avance_enviado

            notify_avance_enviado(
                db,
                actividad_id=1,
                mes=3,
                avance_meta=10,
                actor_username="capturista",
            )

        send_mock.assert_called_once()
        _, kwargs = send_mock.call_args
        assert kwargs["parse_mode"] == "Markdown"
        message = send_mock.call_args.args[1]
        assert "**Nuevo avance enviado a revision**" in message
        assert "Componente: C1 - Componente de prueba" in message
        assert "Actividad: C1.A5 - Actividad de prueba" in message

    def test_notify_avance_revisado_formats_devolucion_with_bold_comment(self):
        db = MagicMock()

        with patch(
            "app.services.notifications.telegram._get_activity_context",
            return_value=self.SAMPLE_CONTEXT,
        ), patch(
            "app.services.notifications.telegram.crud_telegram.get_active_links_by_unidad",
            return_value=[UsuarioTelegramLink(id=1, usuario_id=2, telegram_chat_id="123", is_active=True)],
        ), patch(
            "app.services.notifications.telegram.send_message",
            return_value=True,
        ) as send_mock:
            from app.services.notifications.telegram import notify_avance_revisado

            notify_avance_revisado(
                db,
                actividad_id=1,
                mes=6,
                accion="devolver",
                actor_username="armando-planeacion",
                comentario="No me gusto nada esto",
            )

        message = send_mock.call_args.args[1]
        assert "**Avance devuelto para correccion**" in message
        assert "**Comentario: No me gusto nada esto**" in message
        assert "Componente: C1 - Componente de prueba" in message
        assert "Actividad: C1.A5 - Actividad de prueba" in message
        assert "Revisado por: armando-planeacion" in message

    def test_notify_evidencia_eliminada_includes_bold_file_and_entities(self):
        db = MagicMock()

        with patch(
            "app.services.notifications.telegram._get_activity_context",
            return_value=self.SAMPLE_CONTEXT,
        ), patch(
            "app.services.notifications.telegram.crud_telegram.get_active_links_by_roles",
            return_value=[UsuarioTelegramLink(id=1, usuario_id=2, telegram_chat_id="123", is_active=True)],
        ), patch(
            "app.services.notifications.telegram.send_message",
            return_value=True,
        ) as send_mock:
            from app.services.notifications.telegram import notify_evidencia_eliminada

            notify_evidencia_eliminada(
                db,
                actividad_id=1,
                mes=6,
                nombre_archivo="evidencia.pdf",
                actor_username="capturista",
            )

        message = send_mock.call_args.args[1]
        assert "**Evidencia eliminada**" in message
        assert "**Archivo: evidencia.pdf**" in message
        assert "Componente: C1 - Componente de prueba" in message
        assert "Actividad: C1.A5 - Actividad de prueba" in message
