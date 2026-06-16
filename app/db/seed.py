from calendar import monthrange
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.captura_periodos import CapturaPeriodos
from app.models.ejercicio import Ejercicio

DEFAULT_EJERCICIO_ANIO = 2026


def seed_ejercicio(db: Session, anio: int = DEFAULT_EJERCICIO_ANIO) -> Ejercicio:
    ejercicio = db.query(Ejercicio).filter(Ejercicio.anio == anio).first()
    if ejercicio:
        if not ejercicio.activo:
            db.query(Ejercicio).filter(Ejercicio.id != ejercicio.id).update({"activo": False})
            ejercicio.activo = True
            db.commit()
            db.refresh(ejercicio)
        return ejercicio

    db.query(Ejercicio).update({"activo": False})

    ejercicio = Ejercicio(
        anio=anio,
        fecha_inicio_planeacion=datetime(anio, 1, 1, 0, 0, 0),
        fecha_fin_planeacion=datetime(anio, 12, 31, 23, 59, 59),
        planeacion_abierta=False,
        mostrar_montos=True,
        activo=True,
    )
    db.add(ejercicio)
    db.commit()
    db.refresh(ejercicio)
    return ejercicio


def seed_captura_periodos(db: Session, ejercicio: Ejercicio) -> int:
    existing = (
        db.query(CapturaPeriodos)
        .filter(CapturaPeriodos.ejercicio_id == ejercicio.id)
        .count()
    )
    if existing > 0:
        return 0

    created = 0
    for mes in range(1, 13):
        _, last_day = monthrange(ejercicio.anio, mes)
        periodo = CapturaPeriodos(
            mes=mes,
            fecha_inicio_reporte=datetime(ejercicio.anio, mes, 1, 0, 0, 0),
            fecha_fin_reporte=datetime(ejercicio.anio, mes, last_day, 23, 59, 59),
            ejercicio_id=ejercicio.id,
            activo=True,
        )
        db.add(periodo)
        created += 1

    db.commit()
    return created


def run_seed(anio: int = DEFAULT_EJERCICIO_ANIO) -> None:
    db = SessionLocal()
    try:
        ejercicio = seed_ejercicio(db, anio=anio)
        periodos_creados = seed_captura_periodos(db, ejercicio)
        print(
            f"Seed OK: ejercicio {ejercicio.anio} activo "
            f"(id={ejercicio.id}), periodos_captura_creados={periodos_creados}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
