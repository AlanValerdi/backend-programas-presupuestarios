from pydantic import BaseModel
from typing import Optional, List


class PresupuestoDetalle(BaseModel):
    recursosFiscales: float = 0.0
    participaciones: float = 0.0
    faismun: float = 0.0
    fortamun: float = 0.0
    otros: float = 0.0


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


class ComponenteOut(BaseModel):
    id: int
    programaClave: str
    clave: str
    descripcion: str

    class Config:
        from_attributes = True


class EvidenciaOut(BaseModel):
    id: int
    nombre_original: str
    url_archivo: str
    mime_type: str

    class Config:
        from_attributes = True


class ProgramacionMensualOut(BaseModel):
    mes: str
    mesNumero: int
    meta: int
    estado: str
    avanceMeta: int
    status: str
    evidencias: List[EvidenciaOut] = []
    comentarios: Optional[str] = None


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
