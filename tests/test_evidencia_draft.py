from types import SimpleNamespace

from app.models.programacion_avance import StatusAvance


class TestDraftAvanceCreation:
    def test_create_draft_avance_uses_borrador_status(self):
        from app.crud.programas.avances import create_draft_avance

        db = SimpleNamespace(add=lambda _: None, flush=lambda: None)
        avance = create_draft_avance(db, meta_id=10, avance_meta=5)

        assert avance.programacion_meta_id == 10
        assert avance.avance_meta == 5
        assert avance.status == StatusAvance.BORRADOR
        assert avance.fecha_envio is None


class TestEvidenciaDeleteFlow:
    def test_can_delete_evidencia_only_for_draft_or_correction(self):
        from app.api.routes.programas.evidencia import can_delete_evidencia

        assert can_delete_evidencia(StatusAvance.BORRADOR)
        assert can_delete_evidencia(StatusAvance.CORRECCION)
        assert not can_delete_evidencia(StatusAvance.ENVIADO)
        assert not can_delete_evidencia(StatusAvance.FINALIZADO)
