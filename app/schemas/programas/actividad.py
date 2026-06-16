from typing import List

from pydantic import BaseModel

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

    class Config:
        from_attributes = True
