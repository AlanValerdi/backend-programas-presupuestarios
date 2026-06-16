from sqlalchemy.orm import Session

from app.models.ejercicio import Ejercicio


def get_ejercicio_activo(db: Session) -> Ejercicio | None:
    return db.query(Ejercicio).filter(Ejercicio.activo == True).first()
