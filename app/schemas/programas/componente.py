from pydantic import BaseModel


class ComponenteOut(BaseModel):
    id: int
    programaClave: str
    clave: str
    descripcion: str

    class Config:
        from_attributes = True
