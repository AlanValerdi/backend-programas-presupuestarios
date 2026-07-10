from types import SimpleNamespace

from app.schemas.programas.inputs import EvidenciaDocumentalInput
from app.services.programas.formato_evidencia import (
    _build_evidencia_download_url,
    _format_porcentaje_cumplimiento,
    _format_trimestre_reporte,
    _trimestre_from_mes,
    build_evidencias_documentales,
)


class TestFormatoEvidenciaHelpers:
    def test_trimestre_from_mes(self):
        assert _trimestre_from_mes(1) == 1
        assert _trimestre_from_mes(3) == 1
        assert _trimestre_from_mes(4) == 2
        assert _trimestre_from_mes(12) == 4

    def test_format_trimestre_reporte(self):
        assert (
            _format_trimestre_reporte(1, 2026)
            == "1er Trimestre del Ejercicio Fiscal 2026"
        )
        assert (
            _format_trimestre_reporte(7, 2026)
            == "3er Trimestre del Ejercicio Fiscal 2026"
        )

    def test_format_porcentaje_cumplimiento(self):
        assert (
            _format_porcentaje_cumplimiento(25, 20)
            == "(20 / 25) * 100 = 80.00%"
        )
        assert (
            _format_porcentaje_cumplimiento(0, 10)
            == "(10 / 0) * 100 = N/A"
        )

    def test_build_evidencia_download_url(self):
        assert (
            _build_evidencia_download_url("http://localhost:8000/", 12)
            == "http://localhost:8000/api/programas/evidencia/download/12"
        )

    def test_build_evidencias_documentales_matches_metadata(self):
        evidencia = SimpleNamespace(
            id=5,
            nombre_original="reporte.pdf",
            activo=True,
        )
        avance = SimpleNamespace(evidencias=[evidencia])
        meta = SimpleNamespace(avance=avance)
        metadata = [
            EvidenciaDocumentalInput(
                evidencia_id=5,
                tipo_documento="Acta de entrega",
                folios_referencias="OF-123 / 2026",
            )
        ]

        result = build_evidencias_documentales(
            meta,
            metadata,
            "http://localhost:8000",
        )

        assert len(result) == 1
        assert result[0]["tipo_documento"] == "Acta de entrega"
        assert result[0]["folios_referencias"] == "OF-123 / 2026"
        assert (
            result[0]["ubicacion_archivo"]
            == "http://localhost:8000/api/programas/evidencia/download/5"
        )
        assert result[0]["nombre_archivo"] == "reporte.pdf"

    def test_build_evidencias_documentales_ignores_inactive_files(self):
        active = SimpleNamespace(id=1, nombre_original="a.pdf", activo=True)
        inactive = SimpleNamespace(id=2, nombre_original="b.pdf", activo=False)
        avance = SimpleNamespace(evidencias=[active, inactive])
        meta = SimpleNamespace(avance=avance)

        result = build_evidencias_documentales(meta, [], "http://localhost:8000")

        assert len(result) == 1
        assert result[0]["nombre_archivo"] == "a.pdf"

    def test_build_evidencias_documentales_without_avance(self):
        meta = SimpleNamespace(avance=None)
        result = build_evidencias_documentales(meta, [], "http://localhost:8000")
        assert result == []
