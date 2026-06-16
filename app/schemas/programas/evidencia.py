from pydantic import BaseModel


class EvidenciaOut(BaseModel):
    id: int
    nombre_original: str
    url_archivo: str
    mime_type: str

    class Config:
        from_attributes = True
