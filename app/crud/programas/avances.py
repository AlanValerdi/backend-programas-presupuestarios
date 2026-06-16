import datetime

from sqlalchemy.orm import Session

from app.models.captura_periodos import CapturaPeriodos
from app.models.programacion_avance import ProgramacionAvance, StatusAvance
from app.models.programacion_meta import ProgramacionMeta


def get_programacion_meta(
    db: Session,
    actividad_id: int,
    mes: int,
) -> ProgramacionMeta | None:
    return (
        db.query(ProgramacionMeta)
        .filter(
            ProgramacionMeta.actividad_id == actividad_id,
            ProgramacionMeta.mes == mes,
        )
        .first()
    )


def get_captura_periodo(db: Session, mes: int) -> CapturaPeriodos | None:
    return db.query(CapturaPeriodos).filter(CapturaPeriodos.mes == mes).first()


def get_avance_by_meta_id(db: Session, meta_id: int) -> ProgramacionAvance | None:
    return (
        db.query(ProgramacionAvance)
        .filter(ProgramacionAvance.programacion_meta_id == meta_id)
        .first()
    )


def create_avance(
    db: Session,
    meta_id: int,
    avance_meta: int,
    now: datetime.datetime | None = None,
) -> ProgramacionAvance:
    timestamp = now or datetime.datetime.now()
    avance = ProgramacionAvance(
        programacion_meta_id=meta_id,
        avance_meta=avance_meta,
        status=StatusAvance.ENVIADO,
        fecha_envio=timestamp,
    )
    db.add(avance)
    db.flush()
    return avance
