from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, require_entidad_match, get_db
from app.crud.programas import actividades as actividades_crud
from app.models.programacion_avance import StatusAvance
from app.schemas.programas import ActividadOut
from app.services.programas.formatters import build_actividades_out

router = APIRouter()


@router.get("/actividades/revision", response_model=list[ActividadOut])
def listar_actividades_revision(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
    actividades = actividades_crud.get_actividades_by_avance_status(
        db,
        current_user,
        StatusAvance.ENVIADO,
    )
    return build_actividades_out(actividades)


@router.get("/actividades/revisadas", response_model=list[ActividadOut])
def listar_actividades_revisadas(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_entidad_match),
):
    actividades = actividades_crud.get_actividades_by_avance_status(
        db,
        current_user,
        StatusAvance.FINALIZADO,
    )
    return build_actividades_out(actividades)
