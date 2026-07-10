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
    ("GET", "/api/programas"),
    ("GET", "/api/programas/config/settings"),
    ("PUT", "/api/programas/config/settings"),
    ("GET", "/api/programas/actividades/revision"),
    ("GET", "/api/programas/actividades/revisadas"),
    ("GET", "/api/programas/{clave}"),
    ("PUT", "/api/programas/{clave}/estado"),
    ("GET", "/api/programas/actividades/{actividad_id}"),
    ("GET", "/api/programas/{clave}/componentes"),
    ("GET", "/api/programas/{clave}/actividades"),
    ("POST", "/api/programas/actividades/{actividad_id}/mes/{mes}/avance"),
    ("POST", "/api/programas/actividades/{actividad_id}/mes/{mes}/evidencia-draft"),
    ("POST", "/api/programas/actividades/{actividad_id}/mes/{mes}/formato-evidencia"),
    ("GET", "/api/programas/evidencia/download/{evidencia_id}"),
    ("PUT", "/api/programas/actividades/{actividad_id}/mes/{mes}/revision"),
    ("DELETE", "/api/programas/evidencia/{evidencia_id}"),
    ("GET", "/api/programas/actividades/{actividad_id}/mes/{mes}/trazabilidad"),
    ("GET", "/api/programas/trazabilidad"),
}


def _collect_programas_routes() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        if not hasattr(route, "methods"):
            continue
        path = getattr(route, "path", "")
        if not path.startswith("/api/programas"):
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
        }
        assert expected.issubset(fields)

    def test_programacion_mensual_out_preserves_status_fields(self):
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
        assert expected == fields

    def test_revision_input_accepts_frontend_actions(self):
        assert RevisionInput(accion="aprobar").accion == "aprobar"
        assert RevisionInput(accion="devolver", comentario="fix").comentario == "fix"

    def test_presupuesto_detalle_bucket_fields(self):
        fields = set(PresupuestoDetalle.model_fields.keys())
        assert fields == {
            "recursosFiscales",
            "participaciones",
            "faismun",
            "fortamun",
            "otros",
        }

    def test_componente_out_fields(self):
        fields = set(ComponenteOut.model_fields.keys())
        assert fields == {"id", "programaClave", "clave", "descripcion"}


class TestProgramasFormatters:
    def test_natural_sort_key_orders_numeric_suffixes(self):
        values = ["1.10", "1.2", "1.1"]
        assert sorted(values, key=natural_sort_key) == ["1.1", "1.2", "1.10"]

    def test_month_short_names_cover_twelve_months(self):
        assert len(MESES_NOMBRES_CORTOS) == 12
        assert MESES_NOMBRES_CORTOS[1] == "Ene"
        assert MESES_NOMBRES_CORTOS[12] == "Dic"


class TestFrontendApiPaths:
    """Paths consumed by features/programas/api.ts in the Next.js frontend."""

    FRONTEND_PATHS = [
        "/api/programas",
        "/api/programas/{clave}",
        "/api/programas/{clave}/componentes",
        "/api/programas/{clave}/actividades",
        "/api/programas/{clave}/estado",
        "/api/programas/config/settings",
        "/api/programas/actividades/{actividad_id}",
        "/api/programas/actividades/{actividad_id}/mes/{mes}/avance",
        "/api/programas/actividades/{actividad_id}/mes/{mes}/evidencia-draft",
        "/api/programas/actividades/{actividad_id}/mes/{mes}/formato-evidencia",
        "/api/programas/actividades/{actividad_id}/mes/{mes}/revision",
        "/api/programas/actividades/revision",
        "/api/programas/actividades/revisadas",
        "/api/programas/evidencia/{evidencia_id}",
        "/api/programas/evidencia/download/{evidencia_id}",
        "/api/programas/actividades/{actividad_id}/mes/{mes}/trazabilidad",
        "/api/programas/trazabilidad",
    ]

    def test_frontend_paths_exist_in_openapi(self):
        openapi_paths = set(app.openapi()["paths"].keys())
        for path in self.FRONTEND_PATHS:
            assert path in openapi_paths, f"Missing frontend path: {path}"
