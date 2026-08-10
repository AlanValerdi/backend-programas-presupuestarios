from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_entidad_from_slug, require_any_role, TokenData
from app.models.entidad import Entidad
from app.models.entity_field_contract import EntityFieldContract, EntityType


router = APIRouter(prefix="/contracts", tags=["contracts"])


class FieldContractItem(BaseModel):
    key: str
    label: str
    type: str
    required: bool = False


class FieldContractOut(BaseModel):
    entityType: str
    fields: list[FieldContractItem]


@router.get("/{entity_type}", response_model=FieldContractOut)
def get_contract(
    entity_type: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(require_any_role()),
    entidad: Entidad = Depends(get_entidad_from_slug),
):
    if entity_type not in (EntityType.PROGRAMA, EntityType.ACTIVIDAD):
        raise HTTPException(status_code=400, detail="entity_type must be 'programa' or 'actividad'")

    contract = (
        db.query(EntityFieldContract)
        .filter(
            EntityFieldContract.entidad_id == entidad.id,
            EntityFieldContract.entity_type == entity_type,
        )
        .first()
    )
    fields = contract.fields if contract else []
    return {
        "entityType": entity_type,
        "fields": fields,
    }
