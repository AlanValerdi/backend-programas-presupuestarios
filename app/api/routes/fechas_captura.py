from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from calendar import monthrange
from app.api.dependencies import get_db
from app.models.captura_periodos import CapturaPeriodos
from app.models.ejercicio import Ejercicio
from app.schemas.fechas_captura import FechaCapturaOut


router = APIRouter(prefix="/api/fechas-captura", tags=["fechas_captura"])


class FechaCapturaUpdate(BaseModel):
    fechaInicio: str
    fechaTermino: str


@router.get("", response_model=list[FechaCapturaOut])
def listar_fechas_captura(db: Session = Depends(get_db)):
    # Auto-seed if table is empty
    count = db.query(CapturaPeriodos).count()
    if count == 0:
        ejercicio = db.query(Ejercicio).filter(Ejercicio.activo == True).first()
        if not ejercicio:
            ejercicio = db.query(Ejercicio).first()
        if not ejercicio:
            # Create default 2026 exercise
            ejercicio = Ejercicio(anio=2026, activo=True)
            db.add(ejercicio)
            db.flush()
        
        year = ejercicio.anio
        for m in range(1, 13):
            _, last_day = monthrange(year, m)
            inicio = datetime(year, m, 1, 0, 0, 0)
            fin = datetime(year, m, last_day, 23, 59, 59)
            periodo = CapturaPeriodos(
                mes=m,
                fecha_inicio_reporte=inicio,
                fecha_fin_reporte=fin,
                ejercicio_id=ejercicio.id,
                activo=True
            )
            db.add(periodo)
        db.commit()

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


@router.put("/{id}", response_model=FechaCapturaOut)
def actualizar_fecha_captura(
    id: int,
    data: FechaCapturaUpdate,
    db: Session = Depends(get_db)
):
    periodo = db.query(CapturaPeriodos).filter(CapturaPeriodos.id == id).first()
    if not periodo:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")
        
    def parse_date(date_str: str) -> datetime:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {date_str}. Use MM/DD/YYYY o YYYY-MM-DD.")
        
    periodo.fecha_inicio_reporte = parse_date(data.fechaInicio)
    # Ensure end date is at the end of that day (23:59:59)
    parsed_end = parse_date(data.fechaTermino)
    periodo.fecha_fin_reporte = datetime(parsed_end.year, parsed_end.month, parsed_end.day, 23, 59, 59)
    db.commit()
    db.refresh(periodo)
    
    return {
        "id": periodo.id,
        "mes": _mes_nombre(periodo.mes),
        "mesNumero": periodo.mes,
        "fechaInicio": periodo.fecha_inicio_reporte.strftime("%m/%d/%Y"),
        "fechaTermino": periodo.fecha_fin_reporte.strftime("%m/%d/%Y"),
    }


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
