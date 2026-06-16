from sqlalchemy.orm import Session

from app.models.inter_techo_financiero import TechoFinanciero


def obtener_presupuesto_programa(db: Session, unidad_id: int, ejercicio_id: int) -> dict:
    techos = (
        db.query(TechoFinanciero)
        .filter(
            TechoFinanciero.unidad_administrativa_id == unidad_id,
            TechoFinanciero.ejercicio_id == ejercicio_id,
        )
        .all()
    )

    recursos_fiscales = 0.0
    participaciones = 0.0
    faismun = 0.0
    fortamun = 0.0
    otros = 0.0

    for techo in techos:
        monto = float(techo.monto or 0.0)
        clave = techo.fuente_financiamiento.clave if techo.fuente_financiamiento else ""
        if clave == "1.01":
            recursos_fiscales += monto
        elif clave == "5.01":
            participaciones += monto
        elif clave == "5.02":
            faismun += monto
        elif clave == "5.3":
            fortamun += monto
        else:
            otros += monto

    total = recursos_fiscales + participaciones + faismun + fortamun + otros

    return {
        "presupuestoAsignado": total,
        "presupuesto": {
            "recursosFiscales": recursos_fiscales,
            "participaciones": participaciones,
            "faismun": faismun,
            "fortamun": fortamun,
            "otros": otros,
        },
    }
