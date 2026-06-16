from sqlalchemy.orm import Session

from app.models.programacion_avance import TrazabilidadAvances
from app.models.usuario import Usuario


def registrar_trazabilidad(
    db: Session,
    avance_id: int,
    user_sub: str,
    accion: str,
    detalles: str,
) -> None:
    user = (
        db.query(Usuario)
        .filter((Usuario.email == user_sub) | (Usuario.username == user_sub))
        .first()
    )
    user_id = user.id if user else None
    log = TrazabilidadAvances(
        programacion_avance_id=avance_id,
        usuario_id=user_id,
        accion=accion,
        detalles=detalles,
    )
    db.add(log)
    db.flush()
