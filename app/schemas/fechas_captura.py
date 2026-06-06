from pydantic import BaseModel


class FechaCapturaOut(BaseModel):
    id: int
    mes: str
    mesNumero: int
    fechaInicio: str
    fechaTermino: str

    model_config = {"from_attributes": True}
