from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.programas.evidencia import EvidenciaOut


class ProgramacionMensualOut(BaseModel):
    mes: str
    mesNumero: int
    meta: int
    estado: str
    avanceMeta: int
    status: str
    evidencias: List[EvidenciaOut] = []
    comentarios: Optional[str] = None
    fechaEnvio: Optional[datetime] = None
    fechaRevision: Optional[datetime] = None
