from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.schemas.programas.programacion import ProgramacionMensualOut


class ActividadOut(BaseModel):
    id: int
    programaClave: str
    componenteClave: str
    clave: str
    descripcion: str
    metaAnual: int
    costoEstimado: float
    unidadAdministrativaClave: str
    lineaAccionPmd: str = ""
    programacionMensual: List[ProgramacionMensualOut] = []
    camposExtra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
