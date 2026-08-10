from sqlalchemy.orm import Session

from app.models.ejercicio import Ejercicio


def get_ejercicio_activo(db: Session, entidad_id: int) -> Ejercicio | None:
    return (
        db.query(Ejercicio)
        .filter(Ejercicio.activo == True, Ejercicio.entidad_id == entidad_id)
        .first()
    )
