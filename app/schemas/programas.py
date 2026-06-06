from pydantic import BaseModel


class ProgramaOut(BaseModel):
    id: int
    clave: str
    descripcion: str
    ejecutorClave: str
    ejecutorNombre: str
    ejercicio: int
    fechaCreacion: str
    ultimaActualizacion: str | None

    model_config = {"from_attributes": True}


class ComponenteOut(BaseModel):
    id: int
    programaClave: str
    clave: str
    descripcion: str

    model_config = {"from_attributes": True}


class ActividadOut(BaseModel):
    id: int
    programaClave: str
    componenteClave: str
    clave: str
    descripcion: str
    metaAnual: int
    costoEstimado: float
    unidadAdministrativaClave: str

    model_config = {"from_attributes": True}
