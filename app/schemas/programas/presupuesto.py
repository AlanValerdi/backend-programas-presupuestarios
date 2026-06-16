from pydantic import BaseModel


class PresupuestoDetalle(BaseModel):
    recursosFiscales: float = 0.0
    participaciones: float = 0.0
    faismun: float = 0.0
    fortamun: float = 0.0
    otros: float = 0.0
