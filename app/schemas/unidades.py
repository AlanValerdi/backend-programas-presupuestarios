from pydantic import BaseModel


class UnidadOut(BaseModel):
    id: int
    numero: str
    nombre: str
    plazas: int
    estado: str
    fechaCreacion: str

    model_config = {"from_attributes": True}
