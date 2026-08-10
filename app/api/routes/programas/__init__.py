from fastapi import APIRouter

from app.api.routes.programas import (
    actividades,
    avances,
    catalogo,
    componentes,
    documentos,
    evidencia,
    revision,
    revision_queues,
    settings,
    trazabilidad,
)
from app.schemas.programas import ProgramaOut

router = APIRouter(prefix="/programas", tags=["programas"])

router.add_api_route(
    "",
    catalogo.listar_programas,
    methods=["GET"],
    response_model=list[ProgramaOut],
)
router.include_router(settings.router)
router.include_router(revision_queues.router)
router.include_router(avances.router)
router.include_router(revision.router)
router.include_router(documentos.router)
router.include_router(evidencia.router)
router.include_router(trazabilidad.router)
router.include_router(componentes.router)
router.include_router(actividades.router)
router.include_router(catalogo.router)
