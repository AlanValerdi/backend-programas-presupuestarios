from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.models.captura_periodos import CapturaPeriodos
from app.schemas.fechas_captura import FechaCapturaOut


router = APIRouter(prefix="/api/fechas-captura", tags=["fechas_captura"])


@router.get("", response_model=list[FechaCapturaOut])
def listar_fechas_captura(db: Session = Depends(get_db)):
    periodos = (
        db.query(CapturaPeriodos)
        .order_by(CapturaPeriodos.mes)
        .all()
    )
    return [
        {
            "id": p.id,
            "mes": _mes_nombre(p.mes),
            "mesNumero": p.mes,
            "fechaInicio": p.fecha_inicio_reporte.strftime("%m/%d/%Y")
            if p.fecha_inicio_reporte
            else "",
            "fechaTermino": p.fecha_fin_reporte.strftime("%m/%d/%Y")
            if p.fecha_fin_reporte
            else "",
        }
        for p in periodos
    ]


def _mes_nombre(mes: int) -> str:
    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    if 1 <= mes <= 12:
        return meses[mes - 1]
    return ""
