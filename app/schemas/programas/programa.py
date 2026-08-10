from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

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
    camposExtra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
