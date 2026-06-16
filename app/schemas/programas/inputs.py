from typing import Optional

from pydantic import BaseModel


class RevisionInput(BaseModel):
    accion: str
    comentario: Optional[str] = None
