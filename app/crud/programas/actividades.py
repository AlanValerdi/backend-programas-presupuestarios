from sqlalchemy.orm import Session

from app.api.dependencies import TokenData
from app.models.actividades import Actividades
from app.models.catalogo_programas import CatalogoProgramas
from app.models.componentes import Componentes
from app.models.programacion_avance import ProgramacionAvance, StatusAvance
from app.models.programacion_meta import ProgramacionMeta
from app.models.usuario import RolUsuario


def get_actividades_by_programa_ids(db: Session, programa_ids: list[int]) -> list[Actividades]:
    return (
        db.query(Actividades)
        .join(Componentes, Actividades.componente_id == Componentes.id)
        .filter(Componentes.programa_id.in_(programa_ids))
        .all()
    )


def get_actividad_by_id(db: Session, actividad_id: int) -> Actividades | None:
    return db.query(Actividades).filter(Actividades.id == actividad_id).first()


def get_actividades_by_avance_status(
    db: Session,
    current_user: TokenData,
    status: StatusAvance,
) -> list[Actividades]:
    query = (
        db.query(Actividades)
        .join(Componentes, Actividades.componente_id == Componentes.id)
        .join(CatalogoProgramas, Componentes.programa_id == CatalogoProgramas.id)
    )

    if current_user.rol == RolUsuario.EJECUTOR:
        query = query.filter(
            CatalogoProgramas.unidad_administrativa_id == current_user.unidad_administrativa_id
        )

    query = (
        query.join(ProgramacionMeta, Actividades.id == ProgramacionMeta.actividad_id)
        .join(ProgramacionAvance, ProgramacionMeta.id == ProgramacionAvance.programacion_meta_id)
        .filter(ProgramacionAvance.status == status)
        .distinct()
    )

    return query.all()
