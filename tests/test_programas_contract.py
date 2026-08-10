from app.main import app
from app.schemas.programas import (
    ActividadOut,
    ComponenteOut,
    PresupuestoDetalle,
    ProgramaOut,
    ProgramacionMensualOut,
    RevisionInput,
)
from app.services.programas.formatters import (
    MESES_NOMBRES_CORTOS,
    natural_sort_key,
)

EXPECTED_PROGRAMAS_ROUTES = {
    ("GET", "/api/e/{entidad_slug}/programas"),
    ("GET", "/api/e/{entidad_slug}/programas/config/settings"),
    ("PUT", "/api/e/{entidad_slug}/programas/config/settings"),
    ("GET", "/api/e/{entidad_slug}/programas/actividades/revision"),
    ("GET", "/api/e/{entidad_slug}/programas/actividades/revisadas"),
    ("GET", "/api/e/{entidad_slug}/programas/{clave}"),
    ("PUT", "/api/e/{entidad_slug}/programas/{clave}/estado"),
    ("GET", "/api/e/{entidad_slug}/programas/actividades/{actividad_id}"),
    ("GET", "/api/e/{entidad_slug}/programas/{clave}/componentes"),
    ("GET", "/api/e/{entidad_slug}/programas/{clave}/actividades"),
    ("POST", "/api/e/{entidad_slug}/programas/actividades/{actividad_id}/mes/{mes}/avance"),
    ("POST", "/api/e/{entidad_slug}/programas/actividades/{actividad_id}/mes/{mes}/evidencia-draft"),
    ("POST", "/api/e/{entidad_slug}/programas/actividades/{actividad_id}/mes/{mes}/formato-evidencia"),
    ("GET", "/api/e/{entidad_slug}/programas/evidencia/download/{evidencia_id}"),
    ("PUT", "/api/e/{entidad_slug}/programas/actividades/{actividad_id}/mes/{mes}/revision"),
    ("DELETE", "/api/e/{entidad_slug}/programas/evidencia/{evidencia_id}"),
    ("GET", "/api/e/{entidad_slug}/programas/actividades/{actividad_id}/mes/{mes}/trazabilidad"),
    ("GET", "/api/e/{entidad_slug}/programas/trazabilidad"),
}


def _collect_programas_routes() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        if not hasattr(route, "methods"):
            continue
        path = getattr(route, "path", "")
        if "/programas" not in path:
            continue
        for method in route.methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes.add((method, path))
    return routes


class TestProgramasRouteRegistration:
    def test_all_expected_programas_routes_are_registered(self):
        registered = _collect_programas_routes()
        assert EXPECTED_PROGRAMAS_ROUTES.issubset(registered)


class TestProgramasSchemas:
    def test_programa_out_preserves_frontend_field_names(self):
        fields = set(ProgramaOut.model_fields.keys())
        expected = {
            "id",
            "clave",
            "descripcion",
            "ejecutorClave",
            "ejecutorNombre",
            "ejercicio",
            "fechaCreacion",
            "ultimaActualizacion",
            "presupuestoAsignado",
            "presupuesto",
            "estadoFlujo",
            "camposExtra",
        }
        assert expected.issubset(fields)

    def test_actividad_out_preserves_frontend_field_names(self):
        fields = set(ActividadOut.model_fields.keys())
        expected = {
            "id",
            "programaClave",
            "componenteClave",
            "clave",
            "descripcion",
            "metaAnual",
            "costoEstimado",
            "unidadAdministrativaClave",
            "lineaAccionPmd",
            "programacionMensual",
            "camposExtra",
        }
        assert expected.issubset(fields)

    def test_componente_out_preserves_frontend_field_names(self):
        fields = set(ComponenteOut.model_fields.keys())
        expected = {"id", "programaClave", "clave", "descripcion"}
        assert expected.issubset(fields)

    def test_programacion_mensual_out_preserves_frontend_field_names(self):
        fields = set(ProgramacionMensualOut.model_fields.keys())
        expected = {
            "mes",
            "mesNumero",
            "meta",
            "estado",
            "avanceMeta",
            "status",
            "evidencias",
            "comentarios",
            "fechaEnvio",
            "fechaRevision",
        }
        assert expected.issubset(fields)

    def test_presupuesto_detalle_fields(self):
        fields = set(PresupuestoDetalle.model_fields.keys())
        expected = {
            "recursosFiscales",
            "participaciones",
            "faismun",
            "fortamun",
            "otros",
        }
        assert expected.issubset(fields)

    def test_revision_input_fields(self):
        fields = set(RevisionInput.model_fields.keys())
        assert "accion" in fields
        assert "comentario" in fields


class TestNaturalSort:
    def test_natural_sort_key_orders_numeric_segments(self):
        values = ["10", "2", "1.10", "1.2"]
        sorted_values = sorted(values, key=natural_sort_key)
        assert sorted_values == ["1.2", "1.10", "2", "10"]

    def test_meses_nombres_cortos_complete(self):
        assert len(MESES_NOMBRES_CORTOS) == 12
        assert MESES_NOMBRES_CORTOS[1] == "Ene"
        assert MESES_NOMBRES_CORTOS[12] == "Dic"
