from typing import Optional

from pydantic import BaseModel

from app.schemas.programas.presupuesto import PresupuestoDetalle


class ProgramaOut(BaseModel):
    id: int
    clave: str
    descripcion: str
    ejecutorClave: str
    ejecutorNombre: str
    ejercicio: int
    fechaCreacion: str
    ultimaActualizacion: Optional[str] = None
    presupuestoAsignado: float = 0.0
    presupuesto: PresupuestoDetalle = PresupuestoDetalle()
    estadoFlujo: str = "configuracion"

    class Config:
        from_attributes = True
