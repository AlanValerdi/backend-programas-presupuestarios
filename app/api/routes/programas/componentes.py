from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import TokenData, get_current_user, get_db
from app.crud.programas import catalogo as catalogo_crud
from app.crud.programas import componentes as componentes_crud
from app.schemas.programas import ComponenteOut
from app.services.programas.formatters import build_componentes_out

router = APIRouter()


@router.get("/{clave}/componentes", response_model=list[ComponenteOut])
def listar_componentes(
    clave: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    programas = catalogo_crud.get_programas_by_clave(db, clave, current_user)
    if not programas:
        raise HTTPException(status_code=404, detail="Programa no encontrado")

    prog_ids = [programa.id for programa in programas]
    componentes = componentes_crud.get_componentes_by_programa_ids(db, prog_ids)
    return build_componentes_out(componentes, clave)
