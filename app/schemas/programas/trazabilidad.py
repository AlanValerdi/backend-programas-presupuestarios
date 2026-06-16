from typing import Optional

from pydantic import BaseModel


class TrazabilidadLogOut(BaseModel):
    id: int
    usuario: str
    rol: str
    accion: str
    detalles: str
    creadoEn: str


class TrazabilidadLogGlobalOut(TrazabilidadLogOut):
    mes: int
    actividadClave: str
    componenteClave: str
    programaClave: str
    programaNombre: str
