from sqlalchemy.orm import Session

from app.models.actividades import Actividades
from app.models.catalogo_programas import CatalogoProgramas
from app.models.componentes import Componentes
from app.models.programacion_avance import ProgramacionAvance, TrazabilidadAvances
from app.models.programacion_meta import ProgramacionMeta


def get_trazabilidad_logs_by_avance_id(
    db: Session,
    avance_id: int,
) -> list[TrazabilidadAvances]:
    return (
        db.query(TrazabilidadAvances)
        .filter(TrazabilidadAvances.programacion_avance_id == avance_id)
        .order_by(TrazabilidadAvances.creado_en.desc())
        .all()
    )


def get_trazabilidad_global(db: Session):
    return (
        db.query(
            TrazabilidadAvances,
            ProgramacionMeta.mes,
            Actividades.clave.label("actividad_clave"),
            Componentes.clave.label("componente_clave"),
            CatalogoProgramas.clave.label("programa_clave"),
            CatalogoProgramas.programa.label("programa_nombre"),
        )
        .join(ProgramacionAvance, TrazabilidadAvances.programacion_avance_id == ProgramacionAvance.id)
        .join(ProgramacionMeta, ProgramacionAvance.programacion_meta_id == ProgramacionMeta.id)
        .join(Actividades, ProgramacionMeta.actividad_id == Actividades.id)
        .join(Componentes, Actividades.componente_id == Componentes.id)
        .join(CatalogoProgramas, Componentes.programa_id == CatalogoProgramas.id)
        .order_by(TrazabilidadAvances.creado_en.desc())
        .all()
    )
