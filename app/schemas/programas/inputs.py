from typing import Optional

from pydantic import BaseModel, Field


class RevisionInput(BaseModel):
    accion: str
    comentario: Optional[str] = None


class EvidenciaDocumentalInput(BaseModel):
    evidencia_id: int
    tipo_documento: str = Field(default="", max_length=500)
    folios_referencias: str = Field(default="", max_length=500)


class FormatoEvidenciaInput(BaseModel):
    justificacion_tecnica: str = Field(default="", max_length=5000)
    evidencias: list[EvidenciaDocumentalInput] = Field(default_factory=list)
